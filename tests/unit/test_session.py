from __future__ import annotations

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
