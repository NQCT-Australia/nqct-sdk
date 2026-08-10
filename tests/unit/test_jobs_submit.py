from __future__ import annotations

import json

import httpx
import respx
from nqct import NQCTClient

from tests.fixtures.api_responses import (
    DIRECT_QASM_JOB_ITEM,
    JOB_ID,
    JOB_SUBMIT_RESPONSE,
)

BASE = "http://localhost:8000/api/v1"

QASM = "OPENQASM 3.0;\nqubit[1] q;\nh q[0];"


@respx.mock
def test_submit_job_posts_qasm_and_returns_job() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    job = client.submit_job(
        qasm=QASM,
        backend_id="qiskit-aer-local",
        shots=2048,
        source="api",
        metadata={"label": "bell"},
        fake_backend_name="FakeManilaV2",
    )

    assert route.called
    body = route.calls.last.request.content.decode()
    assert "openqasm3" in body
    assert "FakeManilaV2" in body
    assert job.id == JOB_ID
    assert job.source == "direct_qasm"
    assert job.booking_bypass is False
    client.close()


@respx.mock
def test_submit_job_accepts_pulse_designer_source() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    client.submit_job(
        qasm=QASM,
        backend_id="hardware-qpu-1",
        source="pulse_designer",
    )

    body = json.loads(route.calls.last.request.content.decode())
    assert body["source"] == "pulse_designer"
    client.close()


@respx.mock
def test_submit_job_includes_hardware_qubit_mapping() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    mapping = [{"qreg": "q", "qreg_index": 0, "phyq_index": 2}]
    client.submit_job(
        qasm=QASM,
        backend_id="hardware-qpu-1",
        source="api",
        qubit_mapping=mapping,
    )

    body = json.loads(route.calls.last.request.content.decode())
    assert body["execution_config"]["hardware"]["qubit_mapping"] == mapping
    client.close()


@respx.mock
def test_submit_job_includes_acquisition_type_and_averaging() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    client.submit_job(
        qasm=QASM,
        backend_id="hardware-qpu-1",
        source="api",
        acquisition_type="Discrimination",
        averaging="AverageRepetitions",
    )

    body = json.loads(route.calls.last.request.content.decode())
    hardware = body["execution_config"]["hardware"]
    assert hardware["acquisition_type"] == "Discrimination"
    assert hardware["averaging"] == "AverageRepetitions"
    client.close()


@respx.mock
def test_submit_job_includes_gate_substitutions_and_readout_mapping() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    gate_substitutions = {"cx": "cz"}
    readout_mapping = {"0": "1", "1": "0"}
    client.submit_job(
        qasm=QASM,
        backend_id="hardware-qpu-1",
        source="api",
        gate_substitutions=gate_substitutions,
        readout_mapping=readout_mapping,
    )

    body = json.loads(route.calls.last.request.content.decode())
    hardware = body["execution_config"]["hardware"]
    assert hardware["gate_substitutions"] == gate_substitutions
    assert hardware["readout_mapping"] == readout_mapping
    client.close()


@respx.mock
def test_submit_job_explicit_execution_config_not_merged() -> None:
    client = NQCTClient(url=BASE, api_key="nqct_test")
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json=JOB_SUBMIT_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(
        return_value=httpx.Response(200, json=DIRECT_QASM_JOB_ITEM)
    )

    custom = {"schema_version": 1, "simulator": {"optimization_level": 0}, "hardware": {}}
    client.submit_job(
        qasm=QASM,
        backend_id="qiskit-aer-local",
        execution_config=custom,
        qubit_mapping=[{"qreg": "q", "qreg_index": 0, "phyq_index": 1}],
    )

    body = json.loads(route.calls.last.request.content.decode())
    assert body["execution_config"] == custom
    assert body["execution_config"]["hardware"] == {}
    client.close()
