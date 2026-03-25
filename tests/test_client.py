"""Tests for neonloops.client — NeonloopsClient HTTP layer."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import httpx
import pytest

from neonloops.client import NeonloopsClient
from neonloops.errors import NeonloopsApiError, NeonloopsTimeoutError

API_KEY = "nl_sk_test"
BASE_URL = "https://neonloops.test"


def _make_response(status_code: int, json_data=None, text: str = ""):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    if json_data is not None:
        resp.json.return_value = json_data
        resp.text = json.dumps(json_data)
    else:
        resp.json.side_effect = Exception("no json")
        resp.text = text
    return resp


# --------------------------------------------------------------------------- #
#  Async tests
# --------------------------------------------------------------------------- #

class TestPostAsync:
    @pytest.mark.asyncio
    async def test_success_returns_json(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        expected = {"id": "run_1", "status": "completed"}
        resp = _make_response(200, expected)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            result = await client.post("/api/v1/run", {"input": "hi"})

        assert result == expected
        mock_http.request.assert_called_once()
        call_args = mock_http.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == f"{BASE_URL}/api/v1/run"
        assert call_args[1]["json"] == {"input": "hi"}
        assert "Bearer" in call_args[1]["headers"]["Authorization"]

    @pytest.mark.asyncio
    async def test_error_status_raises_api_error(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
        resp = _make_response(400, {"error": "Bad request"})

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(NeonloopsApiError) as exc_info:
                await client.post("/api/v1/run", {"input": "hi"})

        assert exc_info.value.status == 400
        assert exc_info.value.body == {"error": "Bad request"}

    @pytest.mark.asyncio
    async def test_429_triggers_retry_then_raises(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)
        resp_429 = _make_response(429, {"error": "Rate limited"})

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp_429)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with patch("neonloops.client.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(NeonloopsApiError) as exc_info:
                    await client.post("/api/v1/run", {})

        assert exc_info.value.status == 429
        # Should have been called max_retries + 1 times
        assert mock_http.request.call_count == 2

    @pytest.mark.asyncio
    async def test_429_then_200_succeeds(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)
        resp_429 = _make_response(429, {"error": "Rate limited"})
        resp_200 = _make_response(200, {"status": "ok"})

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=[resp_429, resp_200])
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with patch("neonloops.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.post("/api/v1/run", {})

        assert result == {"status": "ok"}
        assert mock_http.request.call_count == 2

    @pytest.mark.asyncio
    async def test_timeout_raises_timeout_error(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, timeout=5.0)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(NeonloopsTimeoutError) as exc_info:
                await client.post("/api/v1/run", {})

        assert exc_info.value.timeout_s == 5.0


class TestGetAsync:
    @pytest.mark.asyncio
    async def test_success_with_params(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        expected = [{"id": "wf_1"}]
        resp = _make_response(200, expected)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            result = await client.get("/api/v1/workflows", params={"limit": 10})

        assert result == expected
        call_url = mock_http.request.call_args[0][1]
        assert "limit=10" in call_url

    @pytest.mark.asyncio
    async def test_success_no_params(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        expected = [{"id": "wf_1"}]
        resp = _make_response(200, expected)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            result = await client.get("/api/v1/workflows")

        assert result == expected
        call_url = mock_http.request.call_args[0][1]
        assert call_url == f"{BASE_URL}/api/v1/workflows"


class TestPutAsync:
    @pytest.mark.asyncio
    async def test_sends_body(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        resp = _make_response(200, {"id": "wf_1", "name": "Updated"})

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            result = await client.put("/api/v1/workflows/wf_1", {"name": "Updated"})

        assert result["name"] == "Updated"
        call_args = mock_http.request.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[1]["json"] == {"name": "Updated"}


class TestDeleteAsync:
    @pytest.mark.asyncio
    async def test_204_returns_empty_dict(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        resp = _make_response(204)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            result = await client.delete("/api/v1/workflows/wf_1")

        assert result == {}
        assert mock_http.request.call_args[0][0] == "DELETE"


# --------------------------------------------------------------------------- #
#  Sync tests
# --------------------------------------------------------------------------- #

class TestPostSync:
    def test_success_returns_json(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        expected = {"id": "run_1", "status": "completed"}
        resp = _make_response(200, expected)

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            result = client.post_sync("/api/v1/run", {"input": "hi"})

        assert result == expected
        call_args = mock_http.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[1]["json"] == {"input": "hi"}

    def test_error_status_raises_api_error(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
        resp = _make_response(400, {"error": "Bad request"})

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with pytest.raises(NeonloopsApiError) as exc_info:
                client.post_sync("/api/v1/run", {})

        assert exc_info.value.status == 400

    def test_timeout_raises_timeout_error(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, timeout=10.0)

        mock_http = MagicMock()
        mock_http.request = MagicMock(side_effect=httpx.TimeoutException("timeout"))
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with pytest.raises(NeonloopsTimeoutError) as exc_info:
                client.post_sync("/api/v1/run", {})

        assert exc_info.value.timeout_s == 10.0


class TestGetSync:
    def test_success(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        expected = [{"id": "wf_1"}]
        resp = _make_response(200, expected)

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            result = client.get_sync("/api/v1/workflows")

        assert result == expected

    def test_with_params(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        resp = _make_response(200, [])

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            client.get_sync("/api/v1/workflows", params={"project_id": "p1"})

        call_url = mock_http.request.call_args[0][1]
        assert "project_id=p1" in call_url


class TestPutSync:
    def test_sends_body(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        resp = _make_response(200, {"name": "New"})

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            result = client.put_sync("/api/v1/workflows/wf_1", {"name": "New"})

        assert result == {"name": "New"}
        assert mock_http.request.call_args[0][0] == "PUT"


class TestDeleteSync:
    def test_204_returns_empty_dict(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        resp = _make_response(204)

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            result = client.delete_sync("/api/v1/workflows/wf_1")

        assert result == {}


# --------------------------------------------------------------------------- #
#  Streaming tests
# --------------------------------------------------------------------------- #

class TestStreamAsync:
    @pytest.mark.asyncio
    async def test_yields_parsed_events(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        lines = [
            'data: {"type":"run:start","runId":"r1","totalNodes":2}',
            'data: {"type":"run:complete","runId":"r1","status":"completed","durationMs":100}',
        ]

        mock_response = AsyncMock()
        mock_response.status_code = 200

        async def aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = aiter_lines

        mock_http = AsyncMock()
        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = AsyncMock()
        mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_client_ctx):
            events = []
            async for event in client.stream("/api/v1/run/stream", {"input": "hi"}):
                events.append(event)

        assert len(events) == 2
        assert events[0]["type"] == "run:start"
        assert events[0]["runId"] == "r1"
        assert events[1]["type"] == "run:complete"

    @pytest.mark.asyncio
    async def test_error_response_raises(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)

        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.aread = AsyncMock()
        mock_response.json.return_value = {"error": "Server error"}
        mock_response.text = '{"error": "Server error"}'

        mock_http = AsyncMock()
        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = AsyncMock()
        mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_client_ctx):
            with pytest.raises(NeonloopsApiError) as exc_info:
                async for _ in client.stream("/api/v1/run/stream", {}):
                    pass

        assert exc_info.value.status == 500


class TestStreamSync:
    def test_yields_parsed_events(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        lines = [
            'data: {"type":"node:start","runId":"r1","nodeId":"n1","nodeType":"prompt","nodeLabel":"P"}',
            'data: {"type":"run:complete","runId":"r1","status":"completed","durationMs":50}',
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines = MagicMock(return_value=iter(lines))

        mock_http = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_http)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_client_ctx):
            events = list(client.stream_sync("/api/v1/run/stream", {"input": "hi"}))

        assert len(events) == 2
        assert events[0]["type"] == "node:start"
        assert events[1]["type"] == "run:complete"

    def test_error_response_raises(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.read = MagicMock()
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_response.text = '{"error": "Forbidden"}'

        mock_http = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_http)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_client_ctx):
            with pytest.raises(NeonloopsApiError) as exc_info:
                list(client.stream_sync("/api/v1/run/stream", {}))

        assert exc_info.value.status == 403


# --------------------------------------------------------------------------- #
#  URL building
# --------------------------------------------------------------------------- #

class TestBuildUrl:
    def test_no_params(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        url = client._build_url("/api/v1/test")
        assert url == f"{BASE_URL}/api/v1/test"

    def test_with_params(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        url = client._build_url("/api/v1/test", {"limit": 10, "offset": 5})
        assert "limit=10" in url
        assert "offset=5" in url

    def test_none_params_filtered(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)
        url = client._build_url("/api/v1/test", {"limit": 10, "name": None})
        assert "limit=10" in url
        assert "name" not in url

    def test_trailing_slash_stripped(self):
        client = NeonloopsClient(api_key=API_KEY, base_url="https://api.test/")
        url = client._build_url("/path")
        assert url == "https://api.test/path"


# --------------------------------------------------------------------------- #
#  Retry with 500-series status codes
# --------------------------------------------------------------------------- #

class TestRetryBehavior:
    @pytest.mark.asyncio
    async def test_500_retried_then_succeeds(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=2)
        resp_500 = _make_response(500, {"error": "Internal"})
        resp_200 = _make_response(200, {"ok": True})

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=[resp_500, resp_200])
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with patch("neonloops.client.asyncio.sleep", new_callable=AsyncMock):
                result = await client.post("/api/v1/run", {})

        assert result == {"ok": True}
        assert mock_http.request.call_count == 2

    def test_non_retryable_status_not_retried(self):
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=2)
        resp_404 = _make_response(404, {"error": "Not found"})

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp_404)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with pytest.raises(NeonloopsApiError) as exc_info:
                client.post_sync("/api/v1/run", {})

        assert exc_info.value.status == 404
        # Not retried — only 1 call
        assert mock_http.request.call_count == 1


# --------------------------------------------------------------------------- #
#  Headers
# --------------------------------------------------------------------------- #

class TestHeaders:
    def test_authorization_header(self):
        client = NeonloopsClient(api_key="nl_sk_mykey", base_url=BASE_URL)
        headers = client._headers()
        assert headers["Authorization"] == "Bearer nl_sk_mykey"


# --------------------------------------------------------------------------- #
#  Error body parse fallback (json fails → text)
# --------------------------------------------------------------------------- #

def _make_non_json_response(status_code: int, text: str):
    """Build a mock httpx.Response where .json() raises."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.side_effect = Exception("not json")
    resp.text = text
    return resp


class TestErrorBodyFallback:
    @pytest.mark.asyncio
    async def test_async_error_body_falls_back_to_text(self):
        """L77-78: when json() fails, error body should be response.text."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
        resp = _make_non_json_response(400, "plain text error")

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with pytest.raises(NeonloopsApiError) as exc_info:
                await client.post("/api/v1/run", {})

        assert exc_info.value.status == 400
        assert exc_info.value.body == "plain text error"
        assert "API error 400" in str(exc_info.value)

    def test_sync_error_body_falls_back_to_text(self):
        """L145-146: sync path json() fails → text fallback."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=0)
        resp = _make_non_json_response(400, "sync plain error")

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with pytest.raises(NeonloopsApiError) as exc_info:
                client.post_sync("/api/v1/run", {})

        assert exc_info.value.status == 400
        assert exc_info.value.body == "sync plain error"


# --------------------------------------------------------------------------- #
#  Generic exception retry (not Timeout, not ApiError)
# --------------------------------------------------------------------------- #

class TestGenericExceptionRetry:
    @pytest.mark.asyncio
    async def test_async_generic_exception_retries_then_raises(self):
        """L101-108: generic exceptions retry, then raise after max_retries."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=ConnectionError("connection reset"))
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_http):
            with patch("neonloops.client.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(ConnectionError, match="connection reset"):
                    await client.post("/api/v1/run", {})

        assert mock_http.request.call_count == 2

    def test_sync_generic_exception_retries_then_raises(self):
        """L169-176: sync generic exceptions retry, then raise."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)

        mock_http = MagicMock()
        mock_http.request = MagicMock(side_effect=ConnectionError("conn refused"))
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with patch("time.sleep"):
                with pytest.raises(ConnectionError, match="conn refused"):
                    client.post_sync("/api/v1/run", {})

        assert mock_http.request.call_count == 2


# --------------------------------------------------------------------------- #
#  Sync retry with delay (429)
# --------------------------------------------------------------------------- #

class TestSyncRetry:
    def test_sync_429_triggers_retry_then_raises(self):
        """L127-129, L158-161: sync 429 retries with time.sleep delay."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)
        resp_429 = _make_response(429, {"error": "Rate limited"})

        mock_http = MagicMock()
        mock_http.request = MagicMock(return_value=resp_429)
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with patch("time.sleep") as mock_sleep:
                with pytest.raises(NeonloopsApiError) as exc_info:
                    client.post_sync("/api/v1/run", {})

        assert exc_info.value.status == 429
        assert mock_http.request.call_count == 2
        mock_sleep.assert_called_once()

    def test_sync_429_then_200_succeeds(self):
        """Sync retry works: 429 → 200."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL, max_retries=1)
        resp_429 = _make_response(429, {"error": "Rate limited"})
        resp_200 = _make_response(200, {"ok": True})

        mock_http = MagicMock()
        mock_http.request = MagicMock(side_effect=[resp_429, resp_200])
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_http):
            with patch("time.sleep"):
                result = client.post_sync("/api/v1/run", {})

        assert result == {"ok": True}
        assert mock_http.request.call_count == 2


# --------------------------------------------------------------------------- #
#  Stream error with non-JSON body
# --------------------------------------------------------------------------- #

class TestStreamErrorBodyFallback:
    @pytest.mark.asyncio
    async def test_async_stream_non_json_error(self):
        """L232-233: async stream error body json() fails → text fallback."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.aread = AsyncMock()
        mock_response.json.side_effect = Exception("not json")
        mock_response.text = "Internal Server Error"

        mock_http = AsyncMock()
        mock_stream_ctx = AsyncMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = AsyncMock()
        mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("neonloops.client.httpx.AsyncClient", return_value=mock_client_ctx):
            with pytest.raises(NeonloopsApiError) as exc_info:
                async for _ in client.stream("/api/v1/run/stream", {}):
                    pass

        assert exc_info.value.status == 500
        assert exc_info.value.body == "Internal Server Error"
        assert "API error 500" in str(exc_info.value)

    def test_sync_stream_non_json_error(self):
        """L259-260: sync stream error body json() fails → text fallback."""
        client = NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)

        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_response.read = MagicMock()
        mock_response.json.side_effect = Exception("not json")
        mock_response.text = "Bad Gateway"

        mock_http = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_http.stream = MagicMock(return_value=mock_stream_ctx)

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_http)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)

        with patch("neonloops.client.httpx.Client", return_value=mock_client_ctx):
            with pytest.raises(NeonloopsApiError) as exc_info:
                list(client.stream_sync("/api/v1/run/stream", {}))

        assert exc_info.value.status == 502
        assert exc_info.value.body == "Bad Gateway"
