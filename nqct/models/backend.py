"""Backend models aligned with ``GET /backends`` schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from nqct.http.session import HTTPSession
from nqct.models._http import attach_http


class BackendQueueStatus(BaseModel):
    """``GET /backends/{id}/queue`` response."""

    model_config = ConfigDict(extra="ignore")

    backend_id: str
    queue_depth: int
    queued: int
    running: int
    estimated_wait_time_seconds: float
    oldest_queued_wait_time_seconds: float | None = None


class Backend(BaseModel):
    """Backend catalog entry from ``GET /backends`` / ``GET /backends/{id}``."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    provider: str
    type: str
    status: str
    qubits: int
    max_shots: int = 1_000_000
    connectivity: str | None = None
    gates: list[str] | None = None
    noise_model: str | None = None
    topology: str | None = None
    region: str | None = None
    max_duration_hours: int | None = None
    calibration_date: date | None = None
    backend_metadata: dict[str, Any] | None = None
    api_endpoint_url: str | None = Field(
        default=None,
        description="Admin-only field; omitted for regular users.",
    )
    created_at: datetime
    updated_at: datetime

    _http: HTTPSession = PrivateAttr()

    def queue_status(self) -> BackendQueueStatus:
        """``GET /backends/{id}/queue`` — queue depth and wait estimates."""
        response = self._http.get(f"/backends/{self.id}/queue")
        return BackendQueueStatus.model_validate(response.json())


def backend_from_api(data: dict[str, Any], http: HTTPSession) -> Backend:
    """Build a ``Backend`` wired to the HTTP session."""
    backend = Backend.model_validate(data)
    return attach_http(backend, http)
