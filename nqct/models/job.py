"""Job models aligned with ``GET /jobs`` schemas."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PrivateAttr

from nqct.exceptions import JobNotCompleteError
from nqct.execution.polling import wait_for_terminal_status
from nqct.http.session import HTTPSession
from nqct.models._http import attach_http

TERMINAL_STATUSES = frozenset({"done", "failed", "cancelled"})


class Job(BaseModel):
    """Async execution job from function invoke or ``GET /jobs/{id}``."""

    model_config = ConfigDict(extra="ignore")

    id: UUID
    user_id: UUID
    function_name: str
    status: str
    priority: int
    shots: int
    user_username: str | None = None
    user_full_name: str | None = None
    user_email: str | None = None
    function_id: UUID | None = None
    source: str | None = None
    program: dict[str, Any] | None = None
    execution_config: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    backend_id: str | None = None
    qubits: int | None = None
    circuit_depth: int | None = None
    parameters: dict[str, Any] | None = None
    results: dict[str, Any] | None = None
    error_message: str | None = None
    submit_time: datetime
    start_time: datetime | None = None
    end_time: datetime | None = None
    execution_time_seconds: float | None = None
    queue_position: int | None = None
    estimated_wait_time_seconds: float | None = None
    booking_bypass: bool = False
    celery_task_id: str | None = None
    created_at: datetime
    updated_at: datetime

    _http: HTTPSession = PrivateAttr()

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    def refresh(self) -> Job:
        """``GET /jobs/{id}`` — reload job state from the API."""
        response = self._http.get(f"/jobs/{self.id}")
        updated = job_from_api(response.json(), self._http)
        return updated

    def wait(
        self,
        *,
        timeout: float | None = None,
        interval: float = 5.0,
    ) -> Job:
        """Poll ``GET /jobs/{id}`` until a terminal status or timeout.

        Args:
            timeout: Maximum seconds to wait (``None`` = no limit).
            interval: Seconds between polls (default 5, matching Jobs UI).

        Returns:
            The job in a terminal state.

        Raises:
            JobTimeoutError: If ``timeout`` elapses before completion.
            JobFailedError: If the job reaches ``failed`` status.
        """
        return wait_for_terminal_status(self, timeout=timeout, interval=interval)

    def result(self) -> dict[str, Any]:
        """``GET /jobs/{id}/results`` — parsed results when ``status == done``."""
        if self.status != "done":
            raise JobNotCompleteError(
                f"Job {self.id} is {self.status!r}; results are only available when done."
            )
        response = self._http.get(f"/jobs/{self.id}/results")
        payload = response.json()
        results = payload.get("results")
        if results is None:
            return {}
        if not isinstance(results, dict):
            return {"results": results}
        return results

    def cancel(self) -> Job:
        """``DELETE /jobs/{id}`` — cancel a queued or running job."""
        self._http.delete(f"/jobs/{self.id}")
        return self.refresh()

    def logs(self) -> list[str]:
        """``GET /jobs/{id}/logs`` — synthesized execution logs."""
        response = self._http.get(f"/jobs/{self.id}/logs")
        payload = response.json()
        logs = payload.get("logs", [])
        return list(logs) if isinstance(logs, list) else []

    def download_bundle(self, path: str | Path | None = None) -> Path:
        """``GET /jobs/{id}/artifacts/bundle`` — save hardware result zip locally.

        Requires ``status == done``. Missing/skipped artifacts surface as API
        errors (e.g. ``NotFoundError``).

        Args:
            path: Destination file, an *existing* directory, or ``None``
                for ``./job-{id}-hardware-results.zip`` (``~`` expanded).
                A directory target is only detected if it already exists on
                disk; a non-existent path is always treated as the
                destination file itself, so callers must ``mkdir`` any new
                directory before passing it here.

        Returns:
            The resolved (absolute) path to the written zip file.
        """
        if self.status != "done":
            raise JobNotCompleteError(
                f"Job {self.id} is {self.status!r}; artifact bundle is only "
                "available when done."
            )
        default_name = f"job-{self.id}-hardware-results.zip"
        if path is None:
            dest = Path(default_name)
        else:
            dest = Path(path).expanduser()
            if dest.is_dir():
                dest = dest / default_name
        return self._http.stream_to_path(
            f"/jobs/{self.id}/artifacts/bundle", dest
        ).resolve()


def job_from_api(data: dict[str, Any], http: HTTPSession) -> Job:
    """Build a ``Job`` wired to the HTTP session."""
    job = Job.model_validate(data)
    return attach_http(job, http)
