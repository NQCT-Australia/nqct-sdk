"""NQCT Cloud Python client."""

from nqct._version import __version__
from nqct.client import NQCTClient
from nqct.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    JobFailedError,
    JobNotCompleteError,
    JobTimeoutError,
    NotFoundError,
    NQCTError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from nqct.models import Backend, Function, Job

Client = NQCTClient
Runtime = NQCTClient

__all__ = [
    "NQCTClient",
    "Client",
    "Runtime",
    "Backend",
    "Function",
    "Job",
    "NQCTError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "JobFailedError",
    "JobNotCompleteError",
    "JobTimeoutError",
    "__version__",
]
