"""Job polling helpers."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from nqct.exceptions import JobFailedError, JobTimeoutError

if TYPE_CHECKING:
    from nqct.models.job import Job


def wait_for_terminal_status(
    job: Job,
    *,
    timeout: float | None,
    interval: float,
) -> Job:
    """Poll until the job reaches a terminal status or times out."""
    deadline = time.monotonic() + timeout if timeout is not None else None
    current = job

    while not current.is_terminal:
        if deadline is not None and time.monotonic() >= deadline:
            raise JobTimeoutError(
                f"Job {current.id} did not complete within {timeout} seconds "
                f"(last status: {current.status!r})."
            )
        time.sleep(interval)
        current = current.refresh()

    if current.status == "failed":
        message = current.error_message or f"Job {current.id} failed."
        raise JobFailedError(message)

    return current
