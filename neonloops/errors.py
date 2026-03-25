"""Custom exceptions for the Neonloops SDK."""

from __future__ import annotations

from typing import Any, Optional


class NeonloopsApiError(Exception):
    """Raised when the Neonloops API returns a non-OK response."""

    def __init__(
        self,
        message: str,
        status: int,
        body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body

    def __repr__(self) -> str:
        return f"NeonloopsApiError(status={self.status}, message={self!s})"


class NeonloopsTimeoutError(Exception):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, timeout_s: float) -> None:
        super().__init__(f"Request timed out after {timeout_s}s")
        self.timeout_s = timeout_s
