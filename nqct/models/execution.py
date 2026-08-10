"""Execution config models aligned with POST /jobs schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AcquisitionType = Literal["Discrimination", "Integration", "Raw"]
AveragingMode = Literal["AverageRepetitions", "SingleShotCounts"]

_ACQUISITION_TYPES: dict[str, AcquisitionType] = {
    "discrimination": "Discrimination",
    "integration": "Integration",
    "raw": "Raw",
}
_AVERAGING_MODES: dict[str, AveragingMode] = {
    "averagerepetitions": "AverageRepetitions",
    "singleshotcounts": "SingleShotCounts",
}


def normalize_acquisition_type(value: str) -> AcquisitionType:
    """Normalize acquisition_type (case-insensitive) to API PascalCase."""
    key = (value or "").strip().lower()
    if key not in _ACQUISITION_TYPES:
        raise ValueError(
            f"Invalid acquisition_type {value!r}. "
            "Allowed: Discrimination, Integration, Raw"
        )
    return _ACQUISITION_TYPES[key]


def normalize_averaging(value: str) -> AveragingMode:
    """Normalize averaging (case-insensitive) to API PascalCase."""
    key = (value or "").strip().lower()
    if key not in _AVERAGING_MODES:
        raise ValueError(
            f"Invalid averaging {value!r}. "
            "Allowed: AverageRepetitions, SingleShotCounts"
        )
    return _AVERAGING_MODES[key]


class QubitMappingEntry(BaseModel):
    """Logical qreg index → physical qubit."""

    model_config = ConfigDict(extra="forbid")

    qreg: str = Field(..., min_length=1)
    qreg_index: int = Field(..., ge=0)
    phyq_index: int = Field(..., ge=0)


# Callers may pass raw dicts (e.g. loaded from JSON) or already-built models.
QubitMappingLike = dict[str, Any] | QubitMappingEntry


class SimulatorExecutionConfig(BaseModel):
    """Simulator-specific runtime options."""

    model_config = ConfigDict(extra="forbid")

    optimization_level: int = Field(default=1, ge=0, le=3)
    fake_backend_name: str | None = None
    custom_noise_model: dict[str, Any] | None = None


class HardwareExecutionConfig(BaseModel):
    """Hardware runtime options for pull-queue claim payload.

    Optional fields default to ``None`` so that :meth:`model_dump` with
    ``exclude_none=True`` omits them entirely when unset, keeping the
    ``hardware`` envelope as ``{}`` when no hardware options are configured.
    """

    model_config = ConfigDict(extra="forbid")

    qubit_mapping: list[QubitMappingEntry] | None = None
    gate_substitutions: dict[str, Any] | None = None
    acquisition_type: AcquisitionType | None = None
    averaging: AveragingMode | None = None
    readout_mapping: dict[str, Any] | None = None
    pulse_calibration_id: str | None = None
    layout: dict[str, Any] | None = None

    @field_validator("acquisition_type", mode="before")
    @classmethod
    def _normalize_acquisition_type(cls, value: Any) -> AcquisitionType | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return normalize_acquisition_type(str(value))

    @field_validator("averaging", mode="before")
    @classmethod
    def _normalize_averaging(cls, value: Any) -> AveragingMode | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return normalize_averaging(str(value))


class ExecutionConfig(BaseModel):
    """Versioned execution configuration envelope (schema_version 1)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    simulator: SimulatorExecutionConfig = Field(default_factory=SimulatorExecutionConfig)
    hardware: HardwareExecutionConfig = Field(default_factory=HardwareExecutionConfig)
