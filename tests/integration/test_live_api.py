"""Integration tests against a live NQCT Cloud stack.

Run with ``nqct start`` in the sibling ``nqct-cloud`` repo, then::

    export NQCT_URL=http://localhost:8000/api/v1
    export NQCT_API_KEY=nqct_...
    uv run pytest -m integration
"""

from __future__ import annotations

import os

import pytest
from nqct import NQCTClient
from nqct.exceptions import AuthenticationError

pytestmark = pytest.mark.integration


def _require_live_env() -> None:
    if not os.environ.get("NQCT_API_KEY"):
        pytest.skip("NQCT_API_KEY not set — start nqct-cloud and export credentials")
    if not os.environ.get("NQCT_URL"):
        pytest.skip("NQCT_URL not set")


@pytest.fixture
def live_client() -> NQCTClient:
    _require_live_env()
    client = NQCTClient()
    yield client
    client.close()


def test_auth_me(live_client: NQCTClient) -> None:
    profile = live_client.me()
    assert "email" in profile or "username" in profile


def test_list_backends(live_client: NQCTClient) -> None:
    backends = live_client.backends()
    assert isinstance(backends, list)
    for backend in backends:
        assert backend.api_endpoint_url is None


def test_list_jobs(live_client: NQCTClient) -> None:
    jobs = live_client.jobs(limit=10)
    assert isinstance(jobs, list)


def test_list_functions(live_client: NQCTClient) -> None:
    functions = live_client.functions(limit=10)
    assert isinstance(functions, list)


def test_invalid_api_key() -> None:
    _require_live_env()
    url = os.environ["NQCT_URL"]
    client = NQCTClient(url=url, api_key="nqct_invalid_key_for_test")
    try:
        with pytest.raises(AuthenticationError):
            client.me()
    finally:
        client.close()
