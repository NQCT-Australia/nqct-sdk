from __future__ import annotations

import gzip
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import respx
from nqct.exceptions import AuthenticationError, NotFoundError, ServerError, ValidationError
from nqct.http.session import HTTPSession

BASE = "http://localhost:8000/api/v1"


@respx.mock
def test_successful_get() -> None:
    respx.get(f"{BASE}/auth/me").mock(
        return_value=httpx.Response(200, json={"email": "user@example.com"})
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    response = session.get("/auth/me")
    assert response.status_code == 200
    session.close()


@respx.mock
def test_auth_header_sent() -> None:
    route = respx.get(f"{BASE}/auth/me").mock(
        return_value=httpx.Response(200, json={"email": "a@b.c"})
    )
    session = HTTPSession(BASE, api_key="nqct_abc")
    session.get("/auth/me")
    session.close()
    assert route.calls.last.request.headers["x-api-key"] == "nqct_abc"


@respx.mock
def test_maps_401_to_authentication_error() -> None:
    respx.get(f"{BASE}/auth/me").mock(
        return_value=httpx.Response(401, json={"detail": "Could not validate credentials"})
    )
    session = HTTPSession(BASE, api_key="nqct_bad")
    with pytest.raises(AuthenticationError):
        session.get("/auth/me")
    session.close()


@respx.mock
def test_maps_404() -> None:
    respx.get(f"{BASE}/jobs/00000000-0000-0000-0000-000000000001").mock(
        return_value=httpx.Response(404, json={"detail": "Job not found"})
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(NotFoundError):
        session.get("/jobs/00000000-0000-0000-0000-000000000001")
    session.close()


@respx.mock
def test_maps_422() -> None:
    respx.post(f"{BASE}/functions/x/invoke").mock(
        return_value=httpx.Response(422, json={"detail": "invalid"})
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(ValidationError):
        session.request("POST", "/functions/x/invoke", json={})
    session.close()


@respx.mock
def test_maps_500_to_server_error() -> None:
    respx.get(f"{BASE}/backends").mock(return_value=httpx.Response(500, json={"detail": "boom"}))
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(ServerError):
        session.get("/backends")
    session.close()


def test_context_manager() -> None:
    with HTTPSession(BASE, api_key="nqct_test") as session:
        assert session.base_url == BASE


@respx.mock
def test_stream_to_path_writes_bytes(tmp_path: Path) -> None:
    payload = b"PK\x03\x04fake-zip-bytes"
    respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(
            200,
            content=payload,
            headers={
                "Content-Type": "application/zip",
                "Content-Disposition": 'attachment; filename="job-j1-hardware-results.zip"',
            },
        )
    )
    dest = tmp_path / "out.zip"
    session = HTTPSession(BASE, api_key="nqct_test")
    written = session.stream_to_path("/jobs/j1/artifacts/bundle", dest)
    session.close()
    assert written == dest
    assert dest.read_bytes() == payload


@respx.mock
def test_stream_to_path_maps_404(tmp_path: Path) -> None:
    respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(404, json={"detail": "Artifacts not available"})
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(NotFoundError):
        session.stream_to_path("/jobs/j1/artifacts/bundle", tmp_path / "missing.zip")
    session.close()


@respx.mock
def test_stream_to_path_maps_404_with_gzip_content_encoding(tmp_path: Path) -> None:
    """A gzip-encoded error body must not be double-decoded into a DecodingError."""
    compressed = gzip.compress(b'{"detail": "Artifacts not available"}')
    respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(
            404,
            content=compressed,
            headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
        )
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(NotFoundError) as exc_info:
        session.stream_to_path("/jobs/j1/artifacts/bundle", tmp_path / "missing.zip")
    assert exc_info.value.detail == "Artifacts not available"
    session.close()


@respx.mock
def test_stream_to_path_sends_api_key_and_non_json_accept(tmp_path: Path) -> None:
    route = respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=b"zip")
    )
    session = HTTPSession(BASE, api_key="nqct_abc")
    session.stream_to_path("/jobs/j1/artifacts/bundle", tmp_path / "a.zip")
    session.close()
    headers = route.calls.last.request.headers
    assert headers["x-api-key"] == "nqct_abc"
    assert headers["accept"] == "*/*"


@respx.mock
def test_stream_to_path_expands_user_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(200, content=b"zip")
    )
    session = HTTPSession(BASE, api_key="nqct_test")
    dest = Path("~/nested/a.zip")
    written = session.stream_to_path("/jobs/j1/artifacts/bundle", dest.expanduser())
    session.close()
    assert written == tmp_path / "nested" / "a.zip"
    assert written.read_bytes() == b"zip"


class _FailingStream(httpx.SyncByteStream):
    """Yields one chunk then raises, simulating a dropped connection mid-download."""

    def __iter__(self) -> Iterator[bytes]:
        yield b"partial-bytes-before-failure"
        raise httpx.ReadError("connection dropped mid-stream")

    def close(self) -> None:
        pass


@respx.mock
def test_stream_to_path_cleans_up_temp_file_on_mid_stream_failure(tmp_path: Path) -> None:
    respx.get(f"{BASE}/jobs/j1/artifacts/bundle").mock(
        return_value=httpx.Response(200, stream=_FailingStream())
    )
    dest = tmp_path / "out.zip"
    dest.write_bytes(b"previous-good-download")
    session = HTTPSession(BASE, api_key="nqct_test")
    with pytest.raises(httpx.ReadError):
        session.stream_to_path("/jobs/j1/artifacts/bundle", dest)
    session.close()

    # Prior good file at dest must survive a failed re-download attempt.
    assert dest.read_bytes() == b"previous-good-download"
    # No leftover temp/partial files in the destination directory.
    leftovers = [p for p in tmp_path.iterdir() if p != dest]
    assert leftovers == []
