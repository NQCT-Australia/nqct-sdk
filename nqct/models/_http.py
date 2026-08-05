"""Attach HTTP sessions to resource models."""

from __future__ import annotations

from typing import TypeVar

from nqct.http.session import HTTPSession

T = TypeVar("T")


def attach_http(model: T, http: HTTPSession) -> T:
    """Bind an ``HTTPSession`` to a Pydantic model via ``_http`` private attr."""
    object.__setattr__(model, "_http", http)
    return model
