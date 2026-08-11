from __future__ import annotations

import json
import sys
from types import ModuleType
from unittest.mock import MagicMock

import httpx
import pytest
import respx

from tests.fixtures.api_responses import (
    DIRECT_QASM_JOB_ITEM,
    JOB_ID,
    JOB_SUBMIT_RESPONSE,
)

BASE = "http://localhost:8000/api/v1"
QASM = "OPENQASM 3.0;\nqubit[1] q;\nh q[0];"


def _install_quantum_session_stubs() -> None:
    """Stub optional lab deps imported by QuantumSession at module load."""
    _sqd = ModuleType("sqdtoolz")
    _sqd_utils = ModuleType("sqdtoolz.Utilities")
    _sqd_oqasm = ModuleType("sqdtoolz.Utilities.OpenQASM")
    _parser = ModuleType("sqdtoolz.Utilities.OpenQASM.ParserOpenQASM")
    _sched = ModuleType("sqdtoolz.Utilities.OpenQASM.ScheduleParametersJSONConfigZI")
    _file_json = ModuleType("sqdtoolz.Utilities.FileJSON")
    _parser.ParserOpenQASM = MagicMock  # type: ignore[attr-defined]
    _sched.ScheduleParametersJSONConfigZI = MagicMock  # type: ignore[attr-defined]
    _file_json.SerialiseJSON = MagicMock  # type: ignore[attr-defined]
    sys.modules.setdefault("sqdtoolz", _sqd)
    sys.modules.setdefault("sqdtoolz.Utilities", _sqd_utils)
    sys.modules.setdefault("sqdtoolz.Utilities.OpenQASM", _sqd_oqasm)
    sys.modules.setdefault("sqdtoolz.Utilities.OpenQASM.ParserOpenQASM", _parser)
    sys.modules.setdefault(
        "sqdtoolz.Utilities.OpenQASM.ScheduleParametersJSONConfigZI", _sched
    )
    sys.modules.setdefault("sqdtoolz.Utilities.FileJSON", _file_json)
    sys.modules.setdefault("IPython", ModuleType("IPython"))
    _ipy_display = ModuleType("IPython.display")
    _ipy_display.display = MagicMock  # type: ignore[attr-defined]
    _ipy_display.HTML = MagicMock  # type: ignore[attr-defined]
    sys.modules.setdefault("IPython.display", _ipy_display)
    sys.modules.setdefault("pandas", MagicMock())


@pytest.fixture
def quantum_session_cls():
    _install_quantum_session_stubs()
    from nqct.utils.QuantumSession import QuantumSession

    return QuantumSession


@respx.mock
def test_quantum_session_run_passes_acquisition_and_averaging(quantum_session_cls) -> None:
    session = quantum_session_cls(api_key="nqct_test")
    session._client = session._client.__class__(url=BASE, api_key="nqct_test")

    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    done = dict(DIRECT_QASM_JOB_ITEM)
    done["status"] = "done"
    done["results"] = {"counts": {"0": 1}}
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=done))
    respx.get(f"{BASE}/jobs/{JOB_ID}/results").mock(
        return_value=httpx.Response(200, json={"results": {"counts": {"0": 1}}})
    )

    backend = MagicMock()
    backend.id = "hardware-qpu-1"
    backend.type = "simulator"
    session._sel_backend = backend
    session.set_qasm(QASM)
    session.set_acquisition_type("Integration")
    session.set_averaging_type("SingleShotCounts")

    session.run(auto_validate=False)

    body = json.loads(route.calls.last.request.content.decode())
    hardware = body["execution_config"]["hardware"]
    assert hardware["acquisition_type"] == "Integration"
    assert hardware["averaging"] == "SingleShotCounts"
    session.close()


@respx.mock
def test_quantum_session_run_passes_shot_repeat(quantum_session_cls) -> None:
    session = quantum_session_cls(api_key="nqct_test")
    session._client = session._client.__class__(url=BASE, api_key="nqct_test")

    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    done = dict(DIRECT_QASM_JOB_ITEM)
    done["status"] = "done"
    done["results"] = {"counts": {"0": 1}}
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=done))
    respx.get(f"{BASE}/jobs/{JOB_ID}/results").mock(
        return_value=httpx.Response(200, json={"results": {"counts": {"0": 1}}})
    )

    backend = MagicMock()
    backend.id = "hardware-qpu-1"
    backend.type = "simulator"
    session._sel_backend = backend
    session.set_qasm(QASM)
    session.set_shot_repeat(5)

    session.run(auto_validate=False)

    body = json.loads(route.calls.last.request.content.decode())
    assert body["execution_config"]["hardware"]["shot_repeat"] == 5
    session.close()


@pytest.mark.parametrize("shot_repeat", [0, -1, 1.5, "2", True, None])
def test_quantum_session_rejects_invalid_shot_repeat(
    quantum_session_cls, shot_repeat: object
) -> None:
    session = quantum_session_cls(api_key="nqct_test")

    with pytest.raises(ValueError, match="shot_repeat must be an integer >= 1"):
        session.set_shot_repeat(shot_repeat)

    session.close()


def test_quantum_session_max_shots_error_suggests_software_repeats(
    quantum_session_cls, monkeypatch: pytest.MonkeyPatch
) -> None:
    parser = MagicMock()
    parser.check_ZI_max_shots.return_value = 2
    monkeypatch.setattr(
        "nqct.utils.QuantumSession.ParserOpenQASM",
        MagicMock(return_value=parser),
    )

    session = quantum_session_cls(api_key="nqct_test")
    backend = MagicMock()
    backend.type = "hardware"
    backend.backend_metadata = {"topology": {"calibration": {"payload": {}}}}
    session._sel_backend = backend
    session.set_qasm(QASM)
    session.set_num_shots(3)

    with pytest.raises(AssertionError, match=r"set_shot_repeat\(\)"):
        session.validate(print_output=False)

    session.close()


def test_quantum_session_setters_normalize_case(quantum_session_cls) -> None:
    session = quantum_session_cls(api_key="nqct_test")
    session.set_acquisition_type("raw")
    session.set_averaging_type("averagerepetitions")
    assert session._acquisition_type == "Raw"
    assert session._averaging == "AverageRepetitions"
    session.close()
