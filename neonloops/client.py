"""Low-level HTTP client for the Neonloops API."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, Iterator, Optional
from urllib.parse import urlencode

import httpx

from neonloops.errors import NeonloopsApiError, NeonloopsTimeoutError

_DEFAULT_TIMEOUT = 120.0
_DEFAULT_MAX_RETRIES = 2
_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class NeonloopsClient:
    """HTTP client wrapping httpx for Neonloops API calls."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
        }

    # ------------------------------------------------------------------
    # Core request methods
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an authenticated request with retry logic (async)."""
        url = self._build_url(path, params)
        headers = self._headers()
        if body is not None:
            headers["Content-Type"] = "application/json"

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                delay = min(0.5 * (2 ** (attempt - 1)), 8.0)
                await asyncio.sleep(delay)

            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method, url, json=body, headers=headers
                    )

                if response.status_code == 204:
                    return {}

                if response.status_code < 400:
                    return response.json()  # type: ignore[no-any-return]

                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text

                error_msg = (
                    error_body.get("error", f"API error {response.status_code}")
                    if isinstance(error_body, dict)
                    else f"API error {response.status_code}"
                )

                if (
                    response.status_code in _RETRY_STATUS_CODES
                    and attempt < self._max_retries
                ):
                    last_error = NeonloopsApiError(
                        error_msg, response.status_code, error_body
                    )
                    continue

                raise NeonloopsApiError(error_msg, response.status_code, error_body)

            except httpx.TimeoutException:
                raise NeonloopsTimeoutError(self._timeout)
            except NeonloopsApiError:
                raise
            except NeonloopsTimeoutError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise

        raise last_error or RuntimeError("Request failed")

    def _request_sync(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an authenticated request with retry logic (sync)."""
        url = self._build_url(path, params)
        headers = self._headers()
        if body is not None:
            headers["Content-Type"] = "application/json"

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                import time
                delay = min(0.5 * (2 ** (attempt - 1)), 8.0)
                time.sleep(delay)

            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.request(
                        method, url, json=body, headers=headers
                    )

                if response.status_code == 204:
                    return {}

                if response.status_code < 400:
                    return response.json()  # type: ignore[no-any-return]

                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text

                error_msg = (
                    error_body.get("error", f"API error {response.status_code}")
                    if isinstance(error_body, dict)
                    else f"API error {response.status_code}"
                )

                if (
                    response.status_code in _RETRY_STATUS_CODES
                    and attempt < self._max_retries
                ):
                    last_error = NeonloopsApiError(
                        error_msg, response.status_code, error_body
                    )
                    continue

                raise NeonloopsApiError(error_msg, response.status_code, error_body)

            except httpx.TimeoutException:
                raise NeonloopsTimeoutError(self._timeout)
            except NeonloopsApiError:
                raise
            except NeonloopsTimeoutError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise

        raise last_error or RuntimeError("Request failed")

    # ------------------------------------------------------------------
    # Public convenience methods
    # ------------------------------------------------------------------

    async def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Send an authenticated POST request with retry logic."""
        return await self._request("POST", path, body=body)

    def post_sync(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous POST request."""
        return self._request_sync("POST", path, body=body)

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send an authenticated GET request."""
        return await self._request("GET", path, params=params)

    def get_sync(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Synchronous GET request."""
        return self._request_sync("GET", path, params=params)

    async def put(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Send an authenticated PUT request."""
        return await self._request("PUT", path, body=body)

    def put_sync(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous PUT request."""
        return self._request_sync("PUT", path, body=body)

    async def delete(self, path: str) -> Dict[str, Any]:
        """Send an authenticated DELETE request."""
        return await self._request("DELETE", path)

    def delete_sync(self, path: str) -> Dict[str, Any]:
        """Synchronous DELETE request."""
        return self._request_sync("DELETE", path)

    # ------------------------------------------------------------------
    # SSE streaming
    # ------------------------------------------------------------------

    async def stream(self, path: str, body: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """SSE streaming POST — yields parsed JSON dicts. No retry."""
        url = f"{self._base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code >= 400:
                    await response.aread()
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = response.text
                    error_msg = (
                        error_body.get("error", f"API error {response.status_code}")
                        if isinstance(error_body, dict)
                        else f"API error {response.status_code}"
                    )
                    raise NeonloopsApiError(error_msg, response.status_code, error_body)

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield json.loads(line[6:])

    def stream_sync(self, path: str, body: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Synchronous SSE streaming POST — yields parsed JSON dicts. No retry."""
        url = f"{self._base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        with httpx.Client(timeout=self._timeout) as client:
            with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code >= 400:
                    response.read()
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = response.text
                    error_msg = (
                        error_body.get("error", f"API error {response.status_code}")
                        if isinstance(error_body, dict)
                        else f"API error {response.status_code}"
                    )
                    raise NeonloopsApiError(error_msg, response.status_code, error_body)

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        yield json.loads(line[6:])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        url = f"{self._base_url}{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url += f"?{urlencode(filtered)}"
        return url
