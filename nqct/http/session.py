"""httpx session with auth headers and error mapping."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from nqct._version import __version__
from nqct.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    NQCTError,
    RateLimitError,
    ServerError,
    ValidationError,
)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
USER_AGENT = f"nqct-python/{__version__}"


class HTTPSession:
    """Low-level HTTP client for ``/api/v1`` routes."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        token: str | None = None,
        verify_ssl: bool = True,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._token = token
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout or DEFAULT_TIMEOUT,
            verify=verify_ssl,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HTTPSession:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["X-API-Key"] = self._api_key
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> httpx.Response:
        if not path.startswith("/"):
            path = f"/{path}"
        response = self._client.request(
            method,
            path,
            params=params,
            json=json,
            headers=self._auth_headers(),
        )
        if response.is_success:
            return response
        self._raise_for_status(response)
        return response  # pragma: no cover

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> httpx.Response:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> httpx.Response:
        return self.request("POST", path, params=params, json=json)

    def delete(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        return self.request("DELETE", path, params=params)

    def patch(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> httpx.Response:
        return self.request("PATCH", path, params=params, json=json)

    def _raise_for_status(self, response: httpx.Response) -> None:
        detail: Any
        try:
            payload = response.json()
            detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
        except ValueError:
            detail = response.text

        message = _format_error_message(response.status_code, detail)
        exc_map: dict[int, type[NQCTError]] = {
            401: AuthenticationError,
            403: AuthorizationError,
            404: NotFoundError,
            409: ConflictError,
            422: ValidationError,
            429: RateLimitError,
        }
        if response.status_code >= 500:
            raise ServerError(message, status_code=response.status_code, detail=detail)
        exc_type = exc_map.get(response.status_code, NQCTError)
        raise exc_type(message, status_code=response.status_code, detail=detail)


def _format_error_message(status_code: int, detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    return f"HTTP {status_code} from NQCT API"
