"""Backend resource manager — ``GET /backends``."""

from __future__ import annotations

from typing import Any

from nqct.http.session import HTTPSession
from nqct.models.backend import Backend, backend_from_api


class BackendsManager:
    """List and fetch backends."""

    def __init__(self, http: HTTPSession) -> None:
        self._http = http

    def list(
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
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        if provider is not None:
            params["provider"] = provider
        if search is not None:
            params["search"] = search

        response = self._http.get("/backends", params=params)
        payload = response.json()
        items = payload.get("items", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        return [backend_from_api(item, self._http) for item in items]

    def get(self, backend_id: str) -> Backend:
        """``GET /backends/{id}`` — fetch a single backend."""
        response = self._http.get(f"/backends/{backend_id}")
        return backend_from_api(response.json(), self._http)

    def least_busy(self, *, type: str = "simulator") -> Backend:
        """Return the online backend of ``type`` with the lowest queue depth."""
        candidates = self.list(type=type, status="online")
        if not candidates:
            raise LookupError(f"No online backends found for type={type!r}.")

        best = candidates[0]
        best_depth = best.queue_status().queue_depth
        for candidate in candidates[1:]:
            depth = candidate.queue_status().queue_depth
            if depth < best_depth:
                best = candidate
                best_depth = depth
        return best
