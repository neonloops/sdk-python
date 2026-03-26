"""Shared fixtures for Neonloops SDK tests."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest

from neonloops.client import NeonloopsClient


API_KEY = "nl_sk_test_key_123"
BASE_URL = "https://neonloops.test"


# -- Sample API response dicts ------------------------------------------------

WORKFLOW_DICT: Dict[str, Any] = {
    "id": "wf_abc123",
    "project_id": "proj_001",
    "name": "Test Workflow",
    "description": "A test workflow",
    "version": 1,
    "status": "published",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-02T00:00:00Z",
}

WORKFLOW_DETAIL_DICT: Dict[str, Any] = {
    **WORKFLOW_DICT,
    "nodes": [{"id": "n1", "type": "prompt"}],
    "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    "settings": {"timeout": 60},
}

RUN_RESULT_DICT: Dict[str, Any] = {
    "id": "run_xyz789",
    "workflow_id": "wf_abc123",
    "status": "completed",
    "output": "Hello from the workflow!",
    "error": None,
    "approval_prompt": None,
    "paused_at_node_id": None,
    "metadata": {
        "provider": "anthropic",
        "model": "claude-3-opus",
        "tokens": {"input": 100, "output": 50},
        "durationMs": 1500,
        "nodesExecuted": ["n1", "n2"],
    },
}

WORKFLOW_RUN_DICT: Dict[str, Any] = {
    "id": "run_xyz789",
    "workflow_id": "wf_abc123",
    "status": "completed",
    "output": "Hello!",
    "error": None,
    "approval_prompt": None,
    "paused_at_node_id": None,
    "started_at": "2025-01-01T00:00:00Z",
    "completed_at": "2025-01-01T00:00:01Z",
    "created_at": "2025-01-01T00:00:00Z",
}

WORKFLOW_RUN_DETAIL_DICT: Dict[str, Any] = {
    **WORKFLOW_RUN_DICT,
    "workflow_version": 2,
    "input": [{"role": "user", "content": "hi"}],
    "metadata": {"provider": "openai"},
    "node_trace": [{"nodeId": "n1", "status": "ok"}],
}

PROJECT_DICT: Dict[str, Any] = {
    "id": "proj_001",
    "name": "My Project",
    "enabled": True,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-02T00:00:00Z",
}

SECRET_DICT: Dict[str, Any] = {
    "id": "sec_001",
    "name": "OPENAI_API_KEY",
    "created_at": "2025-01-01T00:00:00Z",
}

VERSION_DICT: Dict[str, Any] = {
    "id": "ver_001",
    "workflow_id": "wf_abc123",
    "version": 3,
    "published_at": "2025-03-01T00:00:00Z",
}

PUBLISH_RESULT_DICT: Dict[str, Any] = {
    "version": 4,
    "status": "published",
}

VERSION_DETAIL_DICT: Dict[str, Any] = {
    "id": "ver_001",
    "workflow_id": "wf_abc123",
    "version": 3,
    "published_at": "2025-03-01T00:00:00Z",
    "nodes": [{"id": "n1", "type": "prompt"}],
    "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
}

ROLLBACK_RESULT_DICT: Dict[str, Any] = {
    "version": 2,
    "status": "published",
    "rolled_back_from": 4,
}

SESSION_DICT: Dict[str, Any] = {
    "id": "sess_abc123",
    "workflow_id": "wf_abc123",
    "title": "My Chat",
    "created_at": "2026-03-16T00:00:00.000Z",
    "updated_at": "2026-03-16T01:00:00.000Z",
}

SESSION_MESSAGE_DICT: Dict[str, Any] = {
    "id": "msg_001",
    "session_id": "sess_abc123",
    "role": "user",
    "content": "Hello!",
    "type": "text",
    "created_at": "2026-03-16T00:00:00.000Z",
}


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture
def client() -> NeonloopsClient:
    """A NeonloopsClient instance for testing."""
    return NeonloopsClient(api_key=API_KEY, base_url=BASE_URL)


@pytest.fixture
def mock_client() -> MagicMock:
    """A fully-mocked NeonloopsClient with both async and sync methods."""
    mc = MagicMock(spec=NeonloopsClient)
    mc.get = AsyncMock()
    mc.get_sync = MagicMock()
    mc.post = AsyncMock()
    mc.post_sync = MagicMock()
    mc.put = AsyncMock()
    mc.put_sync = MagicMock()
    mc.delete = AsyncMock()
    mc.delete_sync = MagicMock()
    mc.stream = AsyncMock()
    mc.stream_sync = MagicMock()
    return mc
