"""NQCT SDK exception hierarchy."""

from __future__ import annotations

from typing import Any


class NQCTError(Exception):
    """Base error for all NQCT SDK failures."""

    def __init__(self, message: str, *, status_code: int | None = None, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


class AuthenticationError(NQCTError):
    """Raised when credentials are missing, invalid, or expired (HTTP 401)."""


class AuthorizationError(NQCTError):
    """Raised when the user lacks permission (HTTP 403)."""


class NotFoundError(NQCTError):
    """Raised when a resource does not exist (HTTP 404)."""


class ValidationError(NQCTError):
    """Raised when request validation fails (HTTP 422)."""


class ConflictError(NQCTError):
    """Raised on resource conflicts such as booking overlap (HTTP 409)."""


class RateLimitError(NQCTError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""


class ServerError(NQCTError):
    """Raised on server-side failures (HTTP 5xx)."""


class JobFailedError(NQCTError):
    """Raised when a job reaches ``failed`` status."""


class JobNotCompleteError(NQCTError):
    """Raised when results are requested before a job is ``done``."""


class JobTimeoutError(NQCTError):
    """Raised when ``job.wait()`` exceeds the timeout."""
