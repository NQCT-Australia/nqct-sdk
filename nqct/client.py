"""NQCT Cloud client entry point."""

from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from nqct.auth.credentials import DEFAULT_PROFILE, delete_profile, load_profile, save_profile
from nqct.exceptions import AuthenticationError
from nqct.http.session import HTTPSession
from nqct.models.backend import Backend
from nqct.models.function import Function
from nqct.models.job import Job
from nqct.resources.backends import BackendsManager
from nqct.resources.functions import FunctionsManager
from nqct.resources.jobs import JobsManager, JobSubmitSource, QubitMapping

_ENV_URL = "NQCT_URL"
_ENV_API_KEY = "NQCT_API_KEY"
_ENV_TOKEN = "NQCT_TOKEN"
_ENV_REFRESH_TOKEN = "NQCT_REFRESH_TOKEN"
_ENV_ACCOUNT_NAME = "NQCT_ACCOUNT_NAME"
_ENV_VERIFY_SSL = "NQCT_VERIFY_SSL"

DEFAULT_API_URL = "https://api.nqct.org/api/v1"


class NQCTClient:
    """Client for the NQCT Cloud REST API.

    Maps to platform routes under ``/api/v1``. See the product spec in the
    sibling ``nqct-cloud`` repo: ``references/specs/14-python-sdk.md``.

    Args:
        url: API base URL including ``/api/v1``. Defaults to production
            (``https://api.nqct.org/api/v1``). Override for local ``nqct start``
            (``http://localhost:8000/api/v1``) or via ``NQCT_URL``.
        api_key: ``X-API-Key`` value (``nqct_`` prefix). Preferred for automation.
        token: JWT access token (optional; notebook use).
        refresh_token: JWT refresh token (optional).
        account_name: Named profile in ``~/.nqct/credentials.json``.
        verify_ssl: Verify TLS certificates (default ``True``).
            Set env ``NQCT_VERIFY_SSL=false`` to disable.
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        token: str | None = None,
        refresh_token: str | None = None,
        account_name: str | None = None,
        verify_ssl: bool | None = None,
    ) -> None:
        self._refresh_token = refresh_token
        resolved = _resolve_credentials(
            url=url,
            api_key=api_key,
            token=token,
            refresh_token=refresh_token,
            account_name=account_name,
        )
        self.url = resolved["url"]
        self.api_key = resolved.get("api_key")
        self.token = resolved.get("token")
        self._refresh_token = resolved.get("refresh_token") or self._refresh_token
        if not self.api_key and not self.token:
            raise AuthenticationError(
                "No credentials provided. Set NQCT_API_KEY, pass api_key=, or call save_account()."
            )
        verify = verify_ssl if verify_ssl is not None else _env_verify_ssl()
        self._http = HTTPSession(
            self.url,
            api_key=self.api_key,
            token=self.token,
            verify_ssl=verify,
        )
        self._backends = BackendsManager(self._http)
        self._jobs = JobsManager(self._http)
        self._functions = FunctionsManager(self._http)

    @classmethod
    def save_account(
        cls,
        *,
        api_key: str | None = None,
        url: str | None = None,
        token: str | None = None,
        refresh_token: str | None = None,
        name: str = DEFAULT_PROFILE,
    ) -> None:
        """Save credentials to ``~/.nqct/credentials.json`` (mode ``0600``).

        ``url`` defaults to production (``DEFAULT_API_URL``). Pass a different
        URL for local development.
        """
        save_profile(
            url=url or DEFAULT_API_URL,
            api_key=api_key,
            token=token,
            refresh_token=refresh_token,
            name=name,
        )

    @classmethod
    def delete_account(cls, *, name: str = DEFAULT_PROFILE) -> None:
        """Remove a named profile from the credentials file."""
        delete_profile(name=name)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> NQCTClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def me(self) -> dict[str, Any]:
        """``GET /auth/me`` — current user profile."""
        payload: dict[str, Any] = self._http.get("/auth/me").json()
        return payload

    def backends(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        type: str | None = None,
        status: str | None = None,
        provider: str | None = None,
        search: str | None = None,
    ) -> list[Backend]:
        """``GET /backends`` — list backends with optional filters."""
        return self._backends.list(
            skip=skip,
            limit=limit,
            type=type,
            status=status,
            provider=provider,
            search=search,
        )

    def backend(self, backend_id: str) -> Backend:
        """``GET /backends/{id}`` — fetch a single backend."""
        return self._backends.get(backend_id)

    def least_busy(self, *, type: str = "simulator") -> Backend:
        """Return the online backend with the lowest queue depth."""
        return self._backends.least_busy(type=type)

    def jobs(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        function_id: str | None = None,
        backend_id: str | None = None,
        source: str | None = None,
        user_id: UUID | str | None = None,
    ) -> list[Job]:
        """``GET /jobs`` — list jobs with optional filters."""
        return self._jobs.list(
            skip=skip,
            limit=limit,
            status=status,
            function_id=function_id,
            backend_id=backend_id,
            source=source,
            user_id=user_id,
        )

    def submit_job(
        self,
        *,
        qasm: str,
        backend_id: str,
        shots: int = 1024,
        priority: int = 5,
        source: JobSubmitSource = "direct_qasm",
        execution_config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        fake_backend_name: str | None = None,
        optimization_level: int = 1,
        custom_noise_model: dict[str, Any] | None = None,
        qubit_mapping: QubitMapping | None = None,
        gate_substitutions: dict[str, Any] | None = None,
        acquisition_type: str | None = None,
        averaging: str | None = None,
        readout_mapping: dict[str, Any] | None = None,
        pulse_calibration_id: str | None = None,
    ) -> Job:
        """``POST /jobs`` — submit OpenQASM 3 for async execution on a managed backend.

        Use ``source="api"`` for automation clients that distinguish SDK submits.
        Use ``source="pulse_designer"`` when submitting regenerated OpenPulse QASM
        for hardware execution. If ``execution_config`` is passed explicitly, it is
        sent as-is and the hardware/simulator kwargs (``fake_backend_name``,
        ``optimization_level``, ``custom_noise_model``, ``qubit_mapping``,
        ``gate_substitutions``, ``acquisition_type``, ``averaging``,
        ``readout_mapping``, ``pulse_calibration_id``) are ignored.
        """
        return self._jobs.submit(
            qasm=qasm,
            backend_id=backend_id,
            shots=shots,
            priority=priority,
            source=source,
            execution_config=execution_config,
            metadata=metadata,
            fake_backend_name=fake_backend_name,
            optimization_level=optimization_level,
            custom_noise_model=custom_noise_model,
            qubit_mapping=qubit_mapping,
            gate_substitutions=gate_substitutions,
            acquisition_type=acquisition_type,
            averaging=averaging,
            readout_mapping=readout_mapping,
            pulse_calibration_id=pulse_calibration_id,
        )

    def job(self, job_id: UUID | str) -> Job:
        """``GET /jobs/{id}`` — fetch a single job."""
        return self._jobs.get(job_id)

    def functions(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        sdk_type: str | None = None,
        search: str | None = None,
    ) -> list[Function]:
        """``GET /functions`` — list own and public functions."""
        return self._functions.list(
            skip=skip,
            limit=limit,
            status=status,
            sdk_type=sdk_type,
            search=search,
        )

    def function(self, function_id: UUID | str) -> Function:
        """``GET /functions/{id}`` — fetch a single function."""
        return self._functions.get(function_id)

    @property
    def http(self) -> HTTPSession:
        """Low-level HTTP session (advanced use)."""
        return self._http


def _resolve_credentials(
    *,
    url: str | None,
    api_key: str | None,
    token: str | None,
    refresh_token: str | None,
    account_name: str | None,
) -> dict[str, str]:
    profile_name = account_name or os.environ.get(_ENV_ACCOUNT_NAME, DEFAULT_PROFILE)

    if url is None and api_key is None and token is None:
        try:
            profile = load_profile(profile_name)
            url = profile.get("url")
            api_key = api_key or profile.get("api_key")
            token = token or profile.get("token")
            refresh_token = refresh_token or profile.get("refresh_token")
        except (FileNotFoundError, KeyError):
            pass

    url = url or os.environ.get(_ENV_URL) or DEFAULT_API_URL
    api_key = api_key or os.environ.get(_ENV_API_KEY)
    token = token or os.environ.get(_ENV_TOKEN)
    refresh_token = refresh_token or os.environ.get(_ENV_REFRESH_TOKEN)

    result: dict[str, str] = {"url": url}
    if api_key:
        result["api_key"] = api_key
    if token:
        result["token"] = token
    if refresh_token:
        result["refresh_token"] = refresh_token
    return result


def _env_verify_ssl() -> bool:
    raw = os.environ.get(_ENV_VERIFY_SSL, "true").lower()
    return raw not in {"0", "false", "no"}
