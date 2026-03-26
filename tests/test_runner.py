"""Tests for neonloops.runner — Runner high-level workflow execution."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from neonloops.runner import Runner, ApprovalOptions
from neonloops.types import RunInput, RunResult, RunStartEvent, RunCompleteEvent, Session, SessionMessage
from neonloops.resources import WorkflowsResource, ProjectsResource

from tests.conftest import RUN_RESULT_DICT, SESSION_DICT, SESSION_MESSAGE_DICT


# --------------------------------------------------------------------------- #
#  Constructor
# --------------------------------------------------------------------------- #

class TestRunnerConstructor:
    def test_missing_api_key_raises(self):
        with pytest.raises(ValueError, match="api_key"):
            Runner(api_key="")

    def test_default_values(self):
        r = Runner(api_key="nl_sk_test")
        assert r._client._base_url == "https://neonloops.com"
        assert r._client._timeout == 120.0
        assert r._client._max_retries == 2
        assert r._project_id is None

    def test_custom_values(self):
        r = Runner(
            api_key="nl_sk_test",
            base_url="https://custom.api",
            project_id="proj_1",
            timeout=30.0,
            max_retries=5,
        )
        assert r._client._base_url == "https://custom.api"
        assert r._project_id == "proj_1"
        assert r._client._timeout == 30.0
        assert r._client._max_retries == 5

    def test_resources_initialized(self):
        r = Runner(api_key="nl_sk_test")
        assert isinstance(r.workflows, WorkflowsResource)
        assert isinstance(r.projects, ProjectsResource)


# --------------------------------------------------------------------------- #
#  run() async
# --------------------------------------------------------------------------- #

class TestRunAsync:
    @pytest.mark.asyncio
    async def test_success_returns_run_result(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        result = await r.run(
            workflow_id="wf_abc123",
            input=[RunInput(role="user", content="Hello")],
        )

        assert isinstance(result, RunResult)
        assert result.id == "run_xyz789"
        assert result.workflow_id == "wf_abc123"
        assert result.status == "completed"
        assert result.output == "Hello from the workflow!"
        assert result.error is None
        assert result.metadata.provider == "anthropic"
        assert result.metadata.model == "claude-3-opus"
        assert result.metadata.tokens.input == 100
        assert result.metadata.tokens.output == 50
        assert result.metadata.duration_ms == 1500
        assert result.metadata.nodes_executed == ["n1", "n2"]

        # Verify the request body
        call_args = r._client.post.call_args
        assert call_args[0][0] == "/api/v1/run"
        body = call_args[0][1]
        assert body["workflow_id"] == "wf_abc123"
        assert body["input"] == [{"role": "user", "content": "Hello"}]

    @pytest.mark.asyncio
    async def test_missing_workflow_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="workflow_id"):
            await r.run(
                workflow_id="",
                input=[RunInput(role="user", content="hi")],
            )

    @pytest.mark.asyncio
    async def test_empty_input_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="input"):
            await r.run(workflow_id="wf_1", input=[])

    @pytest.mark.asyncio
    async def test_with_session_id_and_variables(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        await r.run(
            workflow_id="wf_1",
            input=[RunInput(role="user", content="hi")],
            session_id="sess_abc",
            variables={"lang": "en"},
        )

        body = r._client.post.call_args[0][1]
        assert body["session_id"] == "sess_abc"
        assert body["variables"] == {"lang": "en"}

    @pytest.mark.asyncio
    async def test_dict_input_accepted(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        await r.run(
            workflow_id="wf_1",
            input=[{"role": "user", "content": "hi"}],
        )

        body = r._client.post.call_args[0][1]
        assert body["input"] == [{"role": "user", "content": "hi"}]


# --------------------------------------------------------------------------- #
#  run_sync()
# --------------------------------------------------------------------------- #

class TestRunSync:
    def test_success_returns_run_result(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=RUN_RESULT_DICT)

        result = r.run_sync(
            workflow_id="wf_abc123",
            input=[RunInput(role="user", content="Hello")],
        )

        assert isinstance(result, RunResult)
        assert result.id == "run_xyz789"
        assert result.status == "completed"
        assert result.output == "Hello from the workflow!"
        assert result.metadata.provider == "anthropic"

    def test_missing_workflow_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="workflow_id"):
            r.run_sync(workflow_id="", input=[RunInput(role="user", content="hi")])

    def test_empty_input_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="input"):
            r.run_sync(workflow_id="wf_1", input=[])


# --------------------------------------------------------------------------- #
#  run_stream() async
# --------------------------------------------------------------------------- #

class TestRunStreamAsync:
    @pytest.mark.asyncio
    async def test_yields_typed_events(self):
        r = Runner(api_key="nl_sk_test")

        raw_events = [
            {"type": "run:start", "runId": "r1", "totalNodes": 2},
            {"type": "run:complete", "runId": "r1", "status": "completed", "durationMs": 100},
        ]

        async def mock_stream(path, body):
            for e in raw_events:
                yield e

        r._client.stream = mock_stream

        events = []
        async for event in r.run_stream(
            workflow_id="wf_1",
            input=[RunInput(role="user", content="hi")],
        ):
            events.append(event)

        assert len(events) == 2
        assert isinstance(events[0], RunStartEvent)
        assert events[0].run_id == "r1"
        assert events[0].total_nodes == 2
        assert isinstance(events[1], RunCompleteEvent)
        assert events[1].status == "completed"

    @pytest.mark.asyncio
    async def test_missing_workflow_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="workflow_id"):
            async for _ in r.run_stream(workflow_id="", input=[RunInput(role="user", content="hi")]):
                pass

    @pytest.mark.asyncio
    async def test_empty_input_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="input"):
            async for _ in r.run_stream(workflow_id="wf_1", input=[]):
                pass


# --------------------------------------------------------------------------- #
#  run_stream_sync()
# --------------------------------------------------------------------------- #

class TestRunStreamSync:
    def test_missing_workflow_id_raises(self):
        """L128: run_stream_sync validation."""
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="workflow_id"):
            list(r.run_stream_sync(workflow_id="", input=[RunInput(role="user", content="hi")]))

    def test_empty_input_raises(self):
        """L130: run_stream_sync validation."""
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="input"):
            list(r.run_stream_sync(workflow_id="wf_1", input=[]))

    def test_yields_typed_events(self):
        r = Runner(api_key="nl_sk_test")

        raw_events = [
            {"type": "run:start", "runId": "r1", "totalNodes": 2},
            {"type": "run:complete", "runId": "r1", "status": "completed", "durationMs": 100},
        ]

        r._client.stream_sync = MagicMock(return_value=iter(raw_events))

        events = list(r.run_stream_sync(
            workflow_id="wf_1",
            input=[RunInput(role="user", content="hi")],
        ))

        assert len(events) == 2
        assert isinstance(events[0], RunStartEvent)
        assert isinstance(events[1], RunCompleteEvent)


# --------------------------------------------------------------------------- #
#  approve() async
# --------------------------------------------------------------------------- #

class TestApproveAsync:
    @pytest.mark.asyncio
    async def test_success(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        result = await r.approve(run_id="run_xyz789")

        assert isinstance(result, RunResult)
        assert result.id == "run_xyz789"
        r._client.post.assert_called_once_with("/api/v1/run/run_xyz789/approve", {})

    @pytest.mark.asyncio
    async def test_missing_run_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="run_id"):
            await r.approve(run_id="")

    @pytest.mark.asyncio
    async def test_with_comment(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        await r.approve(run_id="run_1", options=ApprovalOptions(comment="Looks good"))

        call_body = r._client.post.call_args[0][1]
        assert call_body == {"comment": "Looks good"}


# --------------------------------------------------------------------------- #
#  approve_sync()
# --------------------------------------------------------------------------- #

class TestApproveSync:
    def test_success(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=RUN_RESULT_DICT)

        result = r.approve_sync(run_id="run_xyz789")

        assert isinstance(result, RunResult)
        assert result.id == "run_xyz789"
        r._client.post_sync.assert_called_once_with(
            "/api/v1/run/run_xyz789/approve", {}
        )

    def test_missing_run_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="run_id"):
            r.approve_sync(run_id="")

    def test_with_comment(self):
        """L171: approve_sync with comment."""
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=RUN_RESULT_DICT)

        r.approve_sync(run_id="run_1", options=ApprovalOptions(comment="LGTM"))

        call_body = r._client.post_sync.call_args[0][1]
        assert call_body == {"comment": "LGTM"}


# --------------------------------------------------------------------------- #
#  reject() async
# --------------------------------------------------------------------------- #

class TestRejectAsync:
    @pytest.mark.asyncio
    async def test_success(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        result = await r.reject(run_id="run_xyz789")

        assert isinstance(result, RunResult)
        r._client.post.assert_called_once_with("/api/v1/run/run_xyz789/reject", {})

    @pytest.mark.asyncio
    async def test_missing_run_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="run_id"):
            await r.reject(run_id="")

    @pytest.mark.asyncio
    async def test_with_comment(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=RUN_RESULT_DICT)

        await r.reject(run_id="run_1", options=ApprovalOptions(comment="Not safe"))

        call_body = r._client.post.call_args[0][1]
        assert call_body == {"comment": "Not safe"}


# --------------------------------------------------------------------------- #
#  reject_sync()
# --------------------------------------------------------------------------- #

class TestRejectSync:
    def test_success(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=RUN_RESULT_DICT)

        result = r.reject_sync(run_id="run_xyz789")

        assert isinstance(result, RunResult)
        r._client.post_sync.assert_called_once_with(
            "/api/v1/run/run_xyz789/reject", {}
        )

    def test_missing_run_id_raises(self):
        r = Runner(api_key="nl_sk_test")
        with pytest.raises(ValueError, match="run_id"):
            r.reject_sync(run_id="")

    def test_with_comment(self):
        """L211: reject_sync with comment."""
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=RUN_RESULT_DICT)

        r.reject_sync(run_id="run_1", options=ApprovalOptions(comment="Nope"))

        call_body = r._client.post_sync.call_args[0][1]
        assert call_body == {"comment": "Nope"}


# --------------------------------------------------------------------------- #
#  _build_body helper
# --------------------------------------------------------------------------- #

class TestBuildBody:
    def test_minimal(self):
        r = Runner(api_key="nl_sk_test")
        body = r._build_body("wf_1", [RunInput(role="user", content="hi")], None, None)
        assert body == {
            "workflow_id": "wf_1",
            "input": [{"role": "user", "content": "hi"}],
        }

    def test_with_all_options(self):
        r = Runner(api_key="nl_sk_test")
        body = r._build_body(
            "wf_1",
            [{"role": "user", "content": "hi"}],
            {"key": "val"},
            "sess_1",
        )
        assert body["workflow_id"] == "wf_1"
        assert body["input"] == [{"role": "user", "content": "hi"}]
        assert body["variables"] == {"key": "val"}
        assert body["session_id"] == "sess_1"


# --------------------------------------------------------------------------- #
#  create_session() async
# --------------------------------------------------------------------------- #

class TestCreateSessionAsync:
    @pytest.mark.asyncio
    async def test_success_with_title(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=SESSION_DICT)

        session = await r.create_session(workflow_id="wf_abc123", title="My Chat")

        assert isinstance(session, Session)
        assert session.id == "sess_abc123"
        assert session.workflow_id == "wf_abc123"
        assert session.title == "My Chat"
        assert session.created_at == "2026-03-16T00:00:00.000Z"
        assert session.updated_at == "2026-03-16T01:00:00.000Z"

        call_args = r._client.post.call_args
        assert call_args[0][0] == "/api/v1/sessions"
        assert call_args[0][1] == {"workflow_id": "wf_abc123", "title": "My Chat"}

    @pytest.mark.asyncio
    async def test_success_without_title(self):
        no_title_dict = {**SESSION_DICT, "title": "New chat"}
        r = Runner(api_key="nl_sk_test")
        r._client.post = AsyncMock(return_value=no_title_dict)

        session = await r.create_session(workflow_id="wf_abc123")

        assert session.title == "New chat"
        call_body = r._client.post.call_args[0][1]
        assert "title" not in call_body


# --------------------------------------------------------------------------- #
#  create_session_sync()
# --------------------------------------------------------------------------- #

class TestCreateSessionSync:
    def test_success(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value=SESSION_DICT)

        session = r.create_session_sync(workflow_id="wf_abc123", title="My Chat")

        assert isinstance(session, Session)
        assert session.id == "sess_abc123"
        assert session.workflow_id == "wf_abc123"
        r._client.post_sync.assert_called_once_with(
            "/api/v1/sessions", {"workflow_id": "wf_abc123", "title": "My Chat"}
        )

    def test_without_title(self):
        r = Runner(api_key="nl_sk_test")
        r._client.post_sync = MagicMock(return_value={**SESSION_DICT, "title": "New chat"})

        session = r.create_session_sync(workflow_id="wf_1")

        call_body = r._client.post_sync.call_args[0][1]
        assert "title" not in call_body


# --------------------------------------------------------------------------- #
#  list_sessions() async
# --------------------------------------------------------------------------- #

class TestListSessionsAsync:
    @pytest.mark.asyncio
    async def test_returns_session_list(self):
        r = Runner(api_key="nl_sk_test")
        paginated_response = {
            "data": [
                SESSION_DICT,
                {**SESSION_DICT, "id": "sess_def456", "title": "Chat 2"},
            ],
            "pagination": {"total": 2, "limit": 50, "offset": 0, "has_more": False},
        }
        r._client.get = AsyncMock(return_value=paginated_response)

        sessions = await r.list_sessions(workflow_id="wf_abc123")

        assert len(sessions.data) == 2
        assert all(isinstance(s, Session) for s in sessions.data)
        assert sessions.data[0].id == "sess_abc123"
        assert sessions.data[1].id == "sess_def456"
        r._client.get.assert_called_once_with(
            "/api/v1/sessions", params={"workflow_id": "wf_abc123"}
        )

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        r = Runner(api_key="nl_sk_test")
        r._client.get = AsyncMock(return_value={
            "data": [],
            "pagination": {"total": 0, "limit": 50, "offset": 0, "has_more": False},
        })

        sessions = await r.list_sessions(workflow_id="wf_empty")

        assert sessions.data == []


# --------------------------------------------------------------------------- #
#  list_sessions_sync()
# --------------------------------------------------------------------------- #

class TestListSessionsSync:
    def test_returns_session_list(self):
        r = Runner(api_key="nl_sk_test")
        r._client.get_sync = MagicMock(return_value={
            "data": [SESSION_DICT],
            "pagination": {"total": 1, "limit": 50, "offset": 0, "has_more": False},
        })

        sessions = r.list_sessions_sync(workflow_id="wf_abc123")

        assert len(sessions.data) == 1
        assert sessions.data[0].id == "sess_abc123"
        r._client.get_sync.assert_called_once_with(
            "/api/v1/sessions", params={"workflow_id": "wf_abc123"}
        )


# --------------------------------------------------------------------------- #
#  get_session_messages() async
# --------------------------------------------------------------------------- #

class TestGetSessionMessagesAsync:
    @pytest.mark.asyncio
    async def test_returns_messages(self):
        r = Runner(api_key="nl_sk_test")
        paginated_response = {
            "data": [
                SESSION_MESSAGE_DICT,
                {
                    **SESSION_MESSAGE_DICT,
                    "id": "msg_002",
                    "role": "assistant",
                    "content": "Hi there!",
                    "created_at": "2026-03-16T00:00:01.000Z",
                },
            ],
            "pagination": {"total": 2, "limit": 100, "offset": 0, "has_more": False},
        }
        r._client.get = AsyncMock(return_value=paginated_response)

        messages = await r.get_session_messages(session_id="sess_abc123")

        assert len(messages) == 2
        assert all(isinstance(m, SessionMessage) for m in messages)
        assert messages[0].id == "msg_001"
        assert messages[0].session_id == "sess_abc123"
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"
        assert messages[0].type == "text"
        assert messages[1].id == "msg_002"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi there!"
        r._client.get.assert_called_once_with(
            "/api/v1/sessions/sess_abc123/messages"
        )

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        r = Runner(api_key="nl_sk_test")
        r._client.get = AsyncMock(return_value={
            "data": [],
            "pagination": {"total": 0, "limit": 100, "offset": 0, "has_more": False},
        })

        messages = await r.get_session_messages(session_id="sess_empty")

        assert messages == []


# --------------------------------------------------------------------------- #
#  get_session_messages_sync()
# --------------------------------------------------------------------------- #

class TestGetSessionMessagesSync:
    def test_returns_messages(self):
        r = Runner(api_key="nl_sk_test")
        r._client.get_sync = MagicMock(return_value={
            "data": [SESSION_MESSAGE_DICT],
            "pagination": {"total": 1, "limit": 100, "offset": 0, "has_more": False},
        })

        messages = r.get_session_messages_sync(session_id="sess_abc123")

        assert len(messages) == 1
        assert messages[0].id == "msg_001"
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"
        r._client.get_sync.assert_called_once_with(
            "/api/v1/sessions/sess_abc123/messages"
        )


# --------------------------------------------------------------------------- #
#  list_sessions() with limit and offset params (L284, L286)
# --------------------------------------------------------------------------- #

class TestListSessionsWithPagination:
    @pytest.mark.asyncio
    async def test_async_with_limit_and_offset(self):
        """L284, L286: list_sessions passes limit and offset params."""
        r = Runner(api_key="nl_sk_test")
        r._client.get = AsyncMock(return_value={
            "data": [SESSION_DICT],
            "pagination": {"total": 1, "limit": 10, "offset": 5, "has_more": False},
        })

        sessions = await r.list_sessions(
            workflow_id="wf_abc123", limit=10, offset=5
        )

        assert len(sessions.data) == 1
        r._client.get.assert_called_once_with(
            "/api/v1/sessions",
            params={"workflow_id": "wf_abc123", "limit": 10, "offset": 5},
        )


# --------------------------------------------------------------------------- #
#  list_sessions_sync() with limit and offset params (L312, L314)
# --------------------------------------------------------------------------- #

class TestListSessionsSyncWithPagination:
    def test_sync_with_limit_and_offset(self):
        """L312, L314: list_sessions_sync passes limit and offset params."""
        r = Runner(api_key="nl_sk_test")
        r._client.get_sync = MagicMock(return_value={
            "data": [SESSION_DICT],
            "pagination": {"total": 1, "limit": 10, "offset": 5, "has_more": False},
        })

        sessions = r.list_sessions_sync(
            workflow_id="wf_abc123", limit=10, offset=5
        )

        assert len(sessions.data) == 1
        r._client.get_sync.assert_called_once_with(
            "/api/v1/sessions",
            params={"workflow_id": "wf_abc123", "limit": 10, "offset": 5},
        )


# --------------------------------------------------------------------------- #
#  _build_body() with version parameter (L362)
# --------------------------------------------------------------------------- #

class TestBuildBodyWithVersion:
    def test_with_version(self):
        """L362: _build_body includes version when provided."""
        r = Runner(api_key="nl_sk_test")
        body = r._build_body(
            "wf_1",
            [RunInput(role="user", content="hi")],
            None,
            None,
            version=3,
        )
        assert body == {
            "workflow_id": "wf_1",
            "input": [{"role": "user", "content": "hi"}],
            "version": 3,
        }
