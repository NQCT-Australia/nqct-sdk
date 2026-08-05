"""Function resource manager — ``GET /functions``."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from nqct.http.session import HTTPSession
from nqct.models.function import Function, function_from_api


class FunctionsManager:
    """List and fetch functions."""

    def __init__(self, http: HTTPSession) -> None:
        self._http = http

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        sdk_type: str | None = None,
        search: str | None = None,
    ) -> list[Function]:
        """``GET /functions`` — list own and public functions."""
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if status is not None:
            params["status"] = status
        if sdk_type is not None:
            params["sdk_type"] = sdk_type
        if search is not None:
            params["search"] = search

        response = self._http.get("/functions", params=params)
        payload = response.json()
        items = payload.get("items", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return []
        return [function_from_api(item, self._http) for item in items]

    def get(self, function_id: UUID | str) -> Function:
        """``GET /functions/{id}`` — fetch a single function."""
        response = self._http.get(f"/functions/{function_id}")
        return function_from_api(response.json(), self._http)
