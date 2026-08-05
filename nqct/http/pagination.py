"""Pagination helpers for list endpoints (Phase 1)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class PageIterator(Generic[T]):
    """Iterate paginated API list responses.

    Concrete resource managers will populate this in Phase 1.
    """

    def __init__(self, items: list[T]) -> None:
        self._items = items

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    @classmethod
    def from_payload(cls, payload: Any) -> PageIterator[Any]:
        if isinstance(payload, list):
            return cls(payload)
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return cls(payload["items"])
        return cls([])
