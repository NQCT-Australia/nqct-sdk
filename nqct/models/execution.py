"""Execution config models aligned with POST /jobs schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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

    ``qubit_mapping`` and ``gate_substitutions`` default to ``None`` (rather
    than an empty list/dict) so that :meth:`model_dump` with
    ``exclude_none=True`` omits them entirely when unset, keeping the
    ``hardware`` envelope as ``{}`` when no hardware options are configured.
    """

    model_config = ConfigDict(extra="forbid")

    qubit_mapping: list[QubitMappingEntry] | None = None
    gate_substitutions: dict[str, Any] | None = None
    readout_mapping: dict[str, Any] | None = None
    pulse_calibration_id: str | None = None
    layout: dict[str, Any] | None = None


class ExecutionConfig(BaseModel):
    """Versioned execution configuration envelope (schema_version 1)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, ge=1)
    simulator: SimulatorExecutionConfig = Field(default_factory=SimulatorExecutionConfig)
    hardware: HardwareExecutionConfig = Field(default_factory=HardwareExecutionConfig)
