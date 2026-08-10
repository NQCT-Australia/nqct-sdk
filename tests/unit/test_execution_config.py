from __future__ import annotations

import pytest
from nqct.models.execution import QubitMappingEntry
from nqct.resources.jobs import build_execution_config
from pydantic import ValidationError


def test_build_execution_config_simulator_defaults() -> None:
    cfg = build_execution_config()
    assert cfg == {
        "schema_version": 1,
        "simulator": {"optimization_level": 1},
        "hardware": {},
    }


def test_build_execution_config_with_qubit_mapping() -> None:
    mapping = [
        {"qreg": "q", "qreg_index": 0, "phyq_index": 1},
        {"qreg": "q", "qreg_index": 1, "phyq_index": 3},
    ]
    cfg = build_execution_config(
        optimization_level=2,
        qubit_mapping=mapping,
        pulse_calibration_id="cal-1",
    )
    assert cfg["schema_version"] == 1
    assert cfg["simulator"]["optimization_level"] == 2
    assert cfg["hardware"]["qubit_mapping"] == mapping
    assert cfg["hardware"]["pulse_calibration_id"] == "cal-1"
    assert "gate_substitutions" not in cfg["hardware"]


def test_build_execution_config_invalid_qubit_mapping_raises() -> None:
    with pytest.raises(ValidationError):
        build_execution_config(qubit_mapping=[{"qreg": "q", "qreg_index": -1, "phyq_index": 0}])


def test_build_execution_config_invalid_qubit_mapping_extra_field_raises() -> None:
    with pytest.raises(ValidationError):
        build_execution_config(
            qubit_mapping=[
                {"qreg": "q", "qreg_index": 0, "phyq_index": 0, "unexpected": "x"}
            ]
        )


def test_build_execution_config_accepts_qubit_mapping_entry_models() -> None:
    entries = [QubitMappingEntry(qreg="q", qreg_index=0, phyq_index=2)]
    cfg = build_execution_config(qubit_mapping=entries)
    assert cfg["hardware"]["qubit_mapping"] == [
        {"qreg": "q", "qreg_index": 0, "phyq_index": 2}
    ]


def test_build_execution_config_hardware_kwargs_all_present() -> None:
    mapping = [{"qreg": "q", "qreg_index": 0, "phyq_index": 1}]
    gate_substitutions = {"cx": "cz"}
    readout_mapping = {"0": "1"}
    cfg = build_execution_config(
        qubit_mapping=mapping,
        gate_substitutions=gate_substitutions,
        readout_mapping=readout_mapping,
        pulse_calibration_id="cal-42",
        acquisition_type="Integration",
        averaging="SingleShotCounts",
    )
    assert cfg["hardware"] == {
        "qubit_mapping": mapping,
        "gate_substitutions": gate_substitutions,
        "readout_mapping": readout_mapping,
        "pulse_calibration_id": "cal-42",
        "acquisition_type": "Integration",
        "averaging": "SingleShotCounts",
    }


def test_build_execution_config_acquisition_and_averaging() -> None:
    cfg = build_execution_config(
        acquisition_type="Discrimination",
        averaging="AverageRepetitions",
    )
    assert cfg["hardware"]["acquisition_type"] == "Discrimination"
    assert cfg["hardware"]["averaging"] == "AverageRepetitions"


def test_build_execution_config_normalizes_acquisition_case() -> None:
    cfg = build_execution_config(acquisition_type="integration", averaging="singleshotcounts")
    assert cfg["hardware"]["acquisition_type"] == "Integration"
    assert cfg["hardware"]["averaging"] == "SingleShotCounts"


def test_build_execution_config_invalid_acquisition_type_raises() -> None:
    with pytest.raises(ValidationError):
        build_execution_config(acquisition_type="Nope")


def test_build_execution_config_invalid_averaging_raises() -> None:
    with pytest.raises(ValidationError):
        build_execution_config(averaging="Nope")


def test_build_execution_config_invalid_optimization_level_raises() -> None:
    with pytest.raises(ValidationError):
        build_execution_config(optimization_level=5)
