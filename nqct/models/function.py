"""Function models aligned with ``GET /functions`` schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PrivateAttr

from nqct.http.session import HTTPSession
from nqct.models._http import attach_http
from nqct.models.job import Job, job_from_api


class Function(BaseModel):
    """Deployed quantum function from ``GET /functions`` / ``GET /functions/{id}``."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    sdk_type: str
    handler_function: str
    author_id: UUID
    status: str
    display_name: str | None = None
    description: str | None = None
    version: str = "1.0.0"
    is_public: bool = False
    author_username: str | None = None
    author_full_name: str | None = None
    code_storage_path: str | None = None
    created_at: datetime
    updated_at: datetime

    _http: HTTPSession = PrivateAttr()

    def invoke(
        self,
        *,
        backend_id: str | None = None,
        backend: str | None = None,
        shots: int = 1024,
        priority: int = 5,
        parameters: dict[str, Any] | None = None,
        fake_backend_name: str | None = None,
    ) -> Job:
        """``POST /functions/{id}/invoke`` — enqueue execution and return a ``Job``."""
        resolved_backend = backend_id or backend
        body: dict[str, Any] = {
            "shots": shots,
            "priority": priority,
            "parameters": parameters or {},
        }
        if resolved_backend is not None:
            body["backend_id"] = resolved_backend
        if fake_backend_name is not None:
            body["fake_backend_name"] = fake_backend_name

        response = self._http.post(f"/functions/{self.id}/invoke", json=body)
        payload = response.json()
        job_id = payload["job_id"]
        job_response = self._http.get(f"/jobs/{job_id}")
        job = job_from_api(job_response.json(), self._http)
        if payload.get("queue_position") is not None:
            job.queue_position = payload["queue_position"]
        return job

    def code(self) -> str:
        """``GET /functions/{id}/code`` — download function source."""
        response = self._http.get(f"/functions/{self.id}/code")
        payload = response.json()
        source = payload.get("code", payload)
        if isinstance(source, str):
            return source
        if isinstance(source, dict) and "code" in source:
            value = source["code"]
            return str(value)
        return str(source)


def function_from_api(data: dict[str, Any], http: HTTPSession) -> Function:
    """Build a ``Function`` wired to the HTTP session."""
    function = Function.model_validate(data)
    return attach_http(function, http)
