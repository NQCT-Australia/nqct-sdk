from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from nqct import NQCTClient
from nqct.exceptions import (
    JobFailedError,
    JobNotCompleteError,
    JobTimeoutError,
    NotFoundError,
)

from tests.fixtures.api_responses import (
    BACKEND_ITEM,
    BACKEND_LIST,
    FUNCTION_CODE,
    FUNCTION_ID,
    FUNCTION_ITEM,
    FUNCTION_LIST,
    INVOKE_RESPONSE,
    JOB_DONE,
    JOB_ID,
    JOB_ITEM,
    JOB_LIST,
    JOB_LOGS,
    JOB_RESULTS,
    QUEUE_STATUS,
)

BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def client() -> NQCTClient:
    return NQCTClient(url=BASE, api_key="nqct_test")


@respx.mock
def test_list_backends(client: NQCTClient) -> None:
    respx.get(f"{BASE}/backends").mock(return_value=httpx.Response(200, json=BACKEND_LIST))
    backends = client.backends()
    assert len(backends) == 1
    assert backends[0].id == "qiskit-aer-local"
    assert backends[0].api_endpoint_url is None
    client.close()


@respx.mock
def test_get_backend(client: NQCTClient) -> None:
    respx.get(f"{BASE}/backends/qiskit-aer-local").mock(
        return_value=httpx.Response(200, json=BACKEND_ITEM)
    )
    backend = client.backend("qiskit-aer-local")
    assert backend.name == "Qiskit Aer Local"
    client.close()


@respx.mock
def test_backend_queue_status(client: NQCTClient) -> None:
    respx.get(f"{BASE}/backends").mock(return_value=httpx.Response(200, json=BACKEND_LIST))
    respx.get(f"{BASE}/backends/qiskit-aer-local/queue").mock(
        return_value=httpx.Response(200, json=QUEUE_STATUS)
    )
    backend = client.backends()[0]
    status = backend.queue_status()
    assert status.queue_depth == 2
    client.close()


@respx.mock
def test_least_busy(client: NQCTClient) -> None:
    busy = {**BACKEND_ITEM, "id": "busy", "name": "Busy"}
    quiet = {**BACKEND_ITEM, "id": "quiet", "name": "Quiet"}
    payload = {**BACKEND_LIST, "items": [busy, quiet], "total": 2}
    respx.get(f"{BASE}/backends").mock(return_value=httpx.Response(200, json=payload))
    busy_queue = {**QUEUE_STATUS, "backend_id": "busy", "queue_depth": 5}
    quiet_queue = {**QUEUE_STATUS, "backend_id": "quiet", "queue_depth": 1}
    respx.get(f"{BASE}/backends/busy/queue").mock(
        return_value=httpx.Response(200, json=busy_queue)
    )
    respx.get(f"{BASE}/backends/quiet/queue").mock(
        return_value=httpx.Response(200, json=quiet_queue)
    )
    picked = client.least_busy()
    assert picked.id == "quiet"
    client.close()


@respx.mock
def test_list_jobs(client: NQCTClient) -> None:
    respx.get(f"{BASE}/jobs").mock(return_value=httpx.Response(200, json=JOB_LIST))
    jobs = client.jobs()
    assert len(jobs) == 1
    assert jobs[0].status == "queued"
    client.close()


@respx.mock
def test_get_job(client: NQCTClient) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    job = client.job(JOB_ID)
    assert job.function_name == "demo-vqe"
    client.close()


@respx.mock
def test_job_result_when_done(client: NQCTClient) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_DONE))
    respx.get(f"{BASE}/jobs/{JOB_ID}/results").mock(
        return_value=httpx.Response(200, json=JOB_RESULTS)
    )
    job = client.job(JOB_ID)
    assert job.result() == {"counts": {"00": 512, "11": 512}}
    client.close()


@respx.mock
def test_job_result_raises_when_not_done(client: NQCTClient) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    job = client.job(JOB_ID)
    with pytest.raises(JobNotCompleteError):
        job.result()
    client.close()


@respx.mock
def test_job_logs(client: NQCTClient) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    respx.get(f"{BASE}/jobs/{JOB_ID}/logs").mock(return_value=httpx.Response(200, json=JOB_LOGS))
    job = client.job(JOB_ID)
    assert job.logs() == ["Job queued", "Job running", "Job completed"]
    client.close()


@respx.mock
def test_job_cancel(client: NQCTClient) -> None:
    cancelled = {**JOB_ITEM, "status": "cancelled"}
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=cancelled))
    respx.delete(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(204))
    job = client.job(JOB_ID)
    updated = job.cancel()
    assert updated.status == "cancelled"
    client.close()


@respx.mock
def test_job_wait_success(client: NQCTClient, monkeypatch: pytest.MonkeyPatch) -> None:
    running = {**JOB_ITEM, "status": "running"}
    route = respx.get(f"{BASE}/jobs/{JOB_ID}")
    route.side_effect = [
        httpx.Response(200, json=JOB_ITEM),
        httpx.Response(200, json=running),
        httpx.Response(200, json=JOB_DONE),
    ]
    monkeypatch.setattr("nqct.execution.polling.time.sleep", lambda _: None)
    job = client.job(JOB_ID)
    finished = job.wait(timeout=30, interval=0.01)
    assert finished.status == "done"
    client.close()


@respx.mock
def test_job_wait_timeout(client: NQCTClient, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    times = iter([0.0, 0.0, 11.0])

    def fake_monotonic() -> float:
        return next(times)

    monkeypatch.setattr("nqct.execution.polling.time.monotonic", fake_monotonic)
    monkeypatch.setattr("nqct.execution.polling.time.sleep", lambda _: None)
    job = client.job(JOB_ID)
    with pytest.raises(JobTimeoutError):
        job.wait(timeout=10, interval=0.01)
    client.close()


@respx.mock
def test_job_wait_failed(client: NQCTClient, monkeypatch: pytest.MonkeyPatch) -> None:
    failed = {**JOB_ITEM, "status": "failed", "error_message": "simulator error"}
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=failed))
    monkeypatch.setattr("nqct.execution.polling.time.sleep", lambda _: None)
    job = client.job(JOB_ID)
    with pytest.raises(JobFailedError, match="simulator error"):
        job.wait(timeout=30, interval=0.01)
    client.close()


@respx.mock
def test_list_functions(client: NQCTClient) -> None:
    respx.get(f"{BASE}/functions").mock(return_value=httpx.Response(200, json=FUNCTION_LIST))
    functions = client.functions()
    assert len(functions) == 1
    assert functions[0].name == "demo-vqe"
    client.close()


@respx.mock
def test_function_invoke(client: NQCTClient) -> None:
    respx.get(f"{BASE}/functions/{FUNCTION_ID}").mock(
        return_value=httpx.Response(200, json=FUNCTION_ITEM)
    )
    respx.post(f"{BASE}/functions/{FUNCTION_ID}/invoke").mock(
        return_value=httpx.Response(200, json=INVOKE_RESPONSE)
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    fn = client.function(FUNCTION_ID)
    job = fn.invoke(backend_id="qiskit-aer-local", shots=2048, parameters={"layers": 2})
    assert job.id == JOB_ID
    assert job.queue_position == 1
    client.close()


@respx.mock
def test_function_code(client: NQCTClient) -> None:
    respx.get(f"{BASE}/functions/{FUNCTION_ID}").mock(
        return_value=httpx.Response(200, json=FUNCTION_ITEM)
    )
    respx.get(f"{BASE}/functions/{FUNCTION_ID}/code").mock(
        return_value=httpx.Response(200, json=FUNCTION_CODE)
    )
    fn = client.function(FUNCTION_ID)
    assert "def run" in fn.code()
    client.close()


@respx.mock
def test_backend_not_found(client: NQCTClient) -> None:
    respx.get(f"{BASE}/backends/missing").mock(
        return_value=httpx.Response(404, json={"detail": "Backend not found"})
    )
    with pytest.raises(NotFoundError):
        client.backend("missing")
    client.close()


@respx.mock
def test_job_download_bundle_writes_zip(client: NQCTClient, tmp_path: Path) -> None:
    zip_bytes = b"PK\x03\x04bundle"
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_DONE))
    respx.get(f"{BASE}/jobs/{JOB_ID}/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=zip_bytes)
    )
    job = client.job(JOB_ID)
    dest = tmp_path / "custom.zip"
    written = job.download_bundle(dest)
    assert written == dest
    assert dest.read_bytes() == zip_bytes
    client.close()


@respx.mock
def test_job_download_bundle_default_name(
    client: NQCTClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    zip_bytes = b"PK\x03\x04bundle"
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_DONE))
    respx.get(f"{BASE}/jobs/{JOB_ID}/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=zip_bytes)
    )
    job = client.job(JOB_ID)
    written = job.download_bundle()
    expected = tmp_path / f"job-{JOB_ID}-hardware-results.zip"
    assert written == expected
    assert expected.read_bytes() == zip_bytes
    client.close()


@respx.mock
def test_job_download_bundle_into_directory(client: NQCTClient, tmp_path: Path) -> None:
    zip_bytes = b"PK\x03\x04bundle"
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_DONE))
    respx.get(f"{BASE}/jobs/{JOB_ID}/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=zip_bytes)
    )
    job = client.job(JOB_ID)
    written = job.download_bundle(tmp_path)
    expected = tmp_path / f"job-{JOB_ID}-hardware-results.zip"
    assert written == expected
    assert expected.read_bytes() == zip_bytes
    client.close()


@respx.mock
def test_job_download_bundle_raises_when_not_done(client: NQCTClient, tmp_path: Path) -> None:
    route = respx.get(f"{BASE}/jobs/{JOB_ID}/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=b"should-not-call")
    )
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_ITEM))
    job = client.job(JOB_ID)
    with pytest.raises(JobNotCompleteError):
        job.download_bundle(tmp_path / "x.zip")
    assert route.call_count == 0
    client.close()


@respx.mock
def test_job_download_bundle_maps_404(client: NQCTClient, tmp_path: Path) -> None:
    respx.get(f"{BASE}/jobs/{JOB_ID}").mock(return_value=httpx.Response(200, json=JOB_DONE))
    respx.get(f"{BASE}/jobs/{JOB_ID}/artifacts/bundle").mock(
        return_value=httpx.Response(404, json={"detail": "Artifacts not available"})
    )
    job = client.job(JOB_ID)
    with pytest.raises(NotFoundError):
        job.download_bundle(tmp_path / "x.zip")
    client.close()
