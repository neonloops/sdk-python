"""Tests for neonloops.resources — WorkflowsResource, ProjectsResource, secrets."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from neonloops.resources import (
    WorkflowsResource,
    WorkflowSecretsResource,
    ProjectsResource,
    ProjectSecretsResource,
)
from neonloops.types import (
    Workflow,
    WorkflowDetail,
    WorkflowRun,
    WorkflowRunDetail,
    WorkflowVersion,
    PublishResult,
    Project,
    Secret,
)

from tests.conftest import (
    WORKFLOW_DICT,
    WORKFLOW_DETAIL_DICT,
    WORKFLOW_RUN_DICT,
    WORKFLOW_RUN_DETAIL_DICT,
    VERSION_DICT,
    PUBLISH_RESULT_DICT,
    PROJECT_DICT,
    SECRET_DICT,
)


# --------------------------------------------------------------------------- #
#  WorkflowsResource
# --------------------------------------------------------------------------- #

class TestWorkflowsList:
    @pytest.mark.asyncio
    async def test_list_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[WORKFLOW_DICT])
        res = WorkflowsResource(mock_client)

        workflows = await res.list()

        assert len(workflows) == 1
        w = workflows[0]
        assert isinstance(w, Workflow)
        assert w.id == "wf_abc123"
        assert w.project_id == "proj_001"
        assert w.name == "Test Workflow"
        assert w.description == "A test workflow"
        assert w.version == 1
        assert w.status == "published"
        mock_client.get.assert_called_once_with("/api/v1/workflows", params=None)

    def test_list_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[WORKFLOW_DICT])
        res = WorkflowsResource(mock_client)

        workflows = res.list_sync()

        assert len(workflows) == 1
        assert isinstance(workflows[0], Workflow)
        assert workflows[0].id == "wf_abc123"

    @pytest.mark.asyncio
    async def test_list_with_params(self, mock_client):
        mock_client.get = AsyncMock(return_value=[])
        res = WorkflowsResource(mock_client)

        await res.list(project_id="p1", limit=10, offset=5)

        mock_client.get.assert_called_once_with(
            "/api/v1/workflows",
            params={"project_id": "p1", "limit": 10, "offset": 5},
        )

    def test_list_sync_with_params(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[])
        res = WorkflowsResource(mock_client)

        res.list_sync(project_id="p1", limit=5)

        call_params = mock_client.get_sync.call_args[1]["params"]
        assert call_params["project_id"] == "p1"
        assert call_params["limit"] == 5

    def test_list_sync_with_offset(self, mock_client):
        """L105: list_sync with offset param."""
        mock_client.get_sync = MagicMock(return_value=[])
        res = WorkflowsResource(mock_client)

        res.list_sync(offset=10)

        call_params = mock_client.get_sync.call_args[1]["params"]
        assert call_params["offset"] == 10


class TestWorkflowsGet:
    @pytest.mark.asyncio
    async def test_get_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = await res.get("wf_abc123")

        assert isinstance(wd, WorkflowDetail)
        assert wd.id == "wf_abc123"
        assert wd.nodes == [{"id": "n1", "type": "prompt"}]
        assert wd.edges == [{"id": "e1", "source": "n1", "target": "n2"}]
        assert wd.settings == {"timeout": 60}
        mock_client.get.assert_called_once_with("/api/v1/workflows/wf_abc123")

    def test_get_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = res.get_sync("wf_abc123")

        assert isinstance(wd, WorkflowDetail)
        assert wd.id == "wf_abc123"


class TestWorkflowsCreate:
    @pytest.mark.asyncio
    async def test_create_async(self, mock_client):
        mock_client.post = AsyncMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = await res.create(
            name="Test Workflow",
            description="A test workflow",
            project_id="proj_001",
        )

        assert isinstance(wd, WorkflowDetail)
        assert wd.name == "Test Workflow"
        call_body = mock_client.post.call_args[0][1]
        assert call_body["name"] == "Test Workflow"
        assert call_body["description"] == "A test workflow"
        assert call_body["projectId"] == "proj_001"

    def test_create_sync(self, mock_client):
        mock_client.post_sync = MagicMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = res.create_sync(name="Test")

        assert isinstance(wd, WorkflowDetail)
        mock_client.post_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_nodes_edges(self, mock_client):
        mock_client.post = AsyncMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        await res.create(nodes=[{"id": "n1"}], edges=[{"id": "e1"}])

        call_body = mock_client.post.call_args[0][1]
        assert call_body["nodes"] == [{"id": "n1"}]
        assert call_body["edges"] == [{"id": "e1"}]

    def test_create_sync_with_all_params(self, mock_client):
        """L155-161: create_sync with description, project_id, nodes, edges."""
        mock_client.post_sync = MagicMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        res.create_sync(
            name="WF",
            description="Desc",
            project_id="p1",
            nodes=[{"id": "n1"}],
            edges=[{"id": "e1"}],
        )

        body = mock_client.post_sync.call_args[0][1]
        assert body["name"] == "WF"
        assert body["description"] == "Desc"
        assert body["projectId"] == "p1"
        assert body["nodes"] == [{"id": "n1"}]
        assert body["edges"] == [{"id": "e1"}]


class TestWorkflowsUpdate:
    @pytest.mark.asyncio
    async def test_update_async(self, mock_client):
        mock_client.put = AsyncMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = await res.update("wf_abc123", name="Updated Name")

        assert isinstance(wd, WorkflowDetail)
        mock_client.put.assert_called_once()
        call_path = mock_client.put.call_args[0][0]
        assert call_path == "/api/v1/workflows/wf_abc123"
        assert mock_client.put.call_args[0][1]["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_async_with_all_params(self, mock_client):
        """L180-186: update with description, nodes, edges, settings."""
        mock_client.put = AsyncMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        await res.update(
            "wf_1",
            name="N",
            description="D",
            nodes="[]",
            edges="[]",
            settings="{}",
        )

        body = mock_client.put.call_args[0][1]
        assert body == {"name": "N", "description": "D", "nodes": "[]", "edges": "[]", "settings": "{}"}

    def test_update_sync(self, mock_client):
        mock_client.put_sync = MagicMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        wd = res.update_sync("wf_abc123", description="New desc")

        assert isinstance(wd, WorkflowDetail)
        assert mock_client.put_sync.call_args[0][1]["description"] == "New desc"

    def test_update_sync_with_all_params(self, mock_client):
        """L201-209: update_sync with all optional params."""
        mock_client.put_sync = MagicMock(return_value=WORKFLOW_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        res.update_sync(
            "wf_1",
            name="N",
            description="D",
            nodes="[]",
            edges="[]",
            settings="{}",
        )

        body = mock_client.put_sync.call_args[0][1]
        assert body == {"name": "N", "description": "D", "nodes": "[]", "edges": "[]", "settings": "{}"}


class TestWorkflowsDelete:
    @pytest.mark.asyncio
    async def test_delete_async(self, mock_client):
        mock_client.delete = AsyncMock(return_value={})
        res = WorkflowsResource(mock_client)

        await res.delete("wf_abc123")

        mock_client.delete.assert_called_once_with("/api/v1/workflows/wf_abc123")

    def test_delete_sync(self, mock_client):
        mock_client.delete_sync = MagicMock(return_value={})
        res = WorkflowsResource(mock_client)

        res.delete_sync("wf_abc123")

        mock_client.delete_sync.assert_called_once_with("/api/v1/workflows/wf_abc123")


class TestWorkflowsPublish:
    @pytest.mark.asyncio
    async def test_publish_async(self, mock_client):
        mock_client.post = AsyncMock(return_value=PUBLISH_RESULT_DICT)
        res = WorkflowsResource(mock_client)

        pr = await res.publish("wf_abc123")

        assert isinstance(pr, PublishResult)
        assert pr.version == 4
        assert pr.status == "published"
        mock_client.post.assert_called_once_with(
            "/api/v1/workflows/wf_abc123/publish", {}
        )

    def test_publish_sync(self, mock_client):
        mock_client.post_sync = MagicMock(return_value=PUBLISH_RESULT_DICT)
        res = WorkflowsResource(mock_client)

        pr = res.publish_sync("wf_abc123")

        assert isinstance(pr, PublishResult)
        assert pr.version == 4

    @pytest.mark.asyncio
    async def test_publish_with_nodes_edges(self, mock_client):
        mock_client.post = AsyncMock(return_value=PUBLISH_RESULT_DICT)
        res = WorkflowsResource(mock_client)

        await res.publish("wf_1", nodes="[nodes]", edges="[edges]")

        body = mock_client.post.call_args[0][1]
        assert body["nodes"] == "[nodes]"
        assert body["edges"] == "[edges]"

    def test_publish_sync_with_nodes_edges(self, mock_client):
        """L247, 249: publish_sync with nodes and edges."""
        mock_client.post_sync = MagicMock(return_value=PUBLISH_RESULT_DICT)
        res = WorkflowsResource(mock_client)

        res.publish_sync("wf_1", nodes="[n]", edges="[e]")

        body = mock_client.post_sync.call_args[0][1]
        assert body["nodes"] == "[n]"
        assert body["edges"] == "[e]"


class TestWorkflowsListVersions:
    @pytest.mark.asyncio
    async def test_list_versions_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[VERSION_DICT])
        res = WorkflowsResource(mock_client)

        versions = await res.list_versions("wf_abc123")

        assert len(versions) == 1
        v = versions[0]
        assert isinstance(v, WorkflowVersion)
        assert v.id == "ver_001"
        assert v.workflow_id == "wf_abc123"
        assert v.version == 3

    def test_list_versions_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[VERSION_DICT])
        res = WorkflowsResource(mock_client)

        versions = res.list_versions_sync("wf_abc123")

        assert len(versions) == 1
        assert isinstance(versions[0], WorkflowVersion)


class TestWorkflowsListRuns:
    @pytest.mark.asyncio
    async def test_list_runs_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[WORKFLOW_RUN_DICT])
        res = WorkflowsResource(mock_client)

        runs = await res.list_runs("wf_abc123")

        assert len(runs) == 1
        r = runs[0]
        assert isinstance(r, WorkflowRun)
        assert r.id == "run_xyz789"
        assert r.workflow_id == "wf_abc123"
        assert r.status == "completed"
        assert r.output == "Hello!"
        assert r.started_at == "2025-01-01T00:00:00Z"

    def test_list_runs_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[WORKFLOW_RUN_DICT])
        res = WorkflowsResource(mock_client)

        runs = res.list_runs_sync("wf_abc123")

        assert len(runs) == 1
        assert isinstance(runs[0], WorkflowRun)

    @pytest.mark.asyncio
    async def test_list_runs_with_pagination(self, mock_client):
        mock_client.get = AsyncMock(return_value=[])
        res = WorkflowsResource(mock_client)

        await res.list_runs("wf_1", limit=10, offset=20)

        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["limit"] == 10
        assert call_params["offset"] == 20

    def test_list_runs_sync_with_pagination(self, mock_client):
        """L291, 293: list_runs_sync with limit and offset."""
        mock_client.get_sync = MagicMock(return_value=[])
        res = WorkflowsResource(mock_client)

        res.list_runs_sync("wf_1", limit=5, offset=10)

        call_params = mock_client.get_sync.call_args[1]["params"]
        assert call_params["limit"] == 5
        assert call_params["offset"] == 10


class TestWorkflowsGetRun:
    @pytest.mark.asyncio
    async def test_get_run_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=WORKFLOW_RUN_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        rd = await res.get_run("wf_abc123", "run_xyz789")

        assert isinstance(rd, WorkflowRunDetail)
        assert rd.id == "run_xyz789"
        assert rd.workflow_version == 2
        assert rd.input == [{"role": "user", "content": "hi"}]
        assert rd.node_trace == [{"nodeId": "n1", "status": "ok"}]
        mock_client.get.assert_called_once_with(
            "/api/v1/workflows/wf_abc123/runs/run_xyz789"
        )

    def test_get_run_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=WORKFLOW_RUN_DETAIL_DICT)
        res = WorkflowsResource(mock_client)

        rd = res.get_run_sync("wf_abc123", "run_xyz789")

        assert isinstance(rd, WorkflowRunDetail)
        assert rd.id == "run_xyz789"


# --------------------------------------------------------------------------- #
#  WorkflowSecretsResource
# --------------------------------------------------------------------------- #

class TestWorkflowSecretsList:
    @pytest.mark.asyncio
    async def test_list_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[SECRET_DICT])
        res = WorkflowSecretsResource(mock_client)

        secrets = await res.list("wf_1")

        assert len(secrets) == 1
        s = secrets[0]
        assert isinstance(s, Secret)
        assert s.id == "sec_001"
        assert s.name == "OPENAI_API_KEY"
        assert s.created_at == "2025-01-01T00:00:00Z"
        mock_client.get.assert_called_once_with("/api/v1/workflows/wf_1/secrets")

    def test_list_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[SECRET_DICT])
        res = WorkflowSecretsResource(mock_client)

        secrets = res.list_sync("wf_1")

        assert len(secrets) == 1
        assert isinstance(secrets[0], Secret)


class TestWorkflowSecretsCreate:
    @pytest.mark.asyncio
    async def test_create_async(self, mock_client):
        mock_client.post = AsyncMock(return_value=SECRET_DICT)
        res = WorkflowSecretsResource(mock_client)

        s = await res.create("wf_1", "OPENAI_API_KEY", "sk-xxx")

        assert isinstance(s, Secret)
        assert s.id == "sec_001"
        mock_client.post.assert_called_once_with(
            "/api/v1/workflows/wf_1/secrets",
            {"name": "OPENAI_API_KEY", "value": "sk-xxx"},
        )

    def test_create_sync(self, mock_client):
        mock_client.post_sync = MagicMock(return_value=SECRET_DICT)
        res = WorkflowSecretsResource(mock_client)

        s = res.create_sync("wf_1", "KEY", "val")

        assert isinstance(s, Secret)
        mock_client.post_sync.assert_called_once_with(
            "/api/v1/workflows/wf_1/secrets",
            {"name": "KEY", "value": "val"},
        )


class TestWorkflowSecretsDelete:
    @pytest.mark.asyncio
    async def test_delete_async(self, mock_client):
        mock_client.delete = AsyncMock(return_value={})
        res = WorkflowSecretsResource(mock_client)

        await res.delete("wf_1", "sec_001")

        mock_client.delete.assert_called_once_with(
            "/api/v1/workflows/wf_1/secrets/sec_001"
        )

    def test_delete_sync(self, mock_client):
        mock_client.delete_sync = MagicMock(return_value={})
        res = WorkflowSecretsResource(mock_client)

        res.delete_sync("wf_1", "sec_001")

        mock_client.delete_sync.assert_called_once_with(
            "/api/v1/workflows/wf_1/secrets/sec_001"
        )


# --------------------------------------------------------------------------- #
#  ProjectsResource
# --------------------------------------------------------------------------- #

class TestProjectsList:
    @pytest.mark.asyncio
    async def test_list_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[PROJECT_DICT])
        res = ProjectsResource(mock_client)

        projects = await res.list()

        assert len(projects) == 1
        p = projects[0]
        assert isinstance(p, Project)
        assert p.id == "proj_001"
        assert p.name == "My Project"
        assert p.enabled is True
        assert p.created_at == "2025-01-01T00:00:00Z"
        assert p.updated_at == "2025-01-02T00:00:00Z"
        mock_client.get.assert_called_once_with("/api/v1/projects")

    def test_list_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[PROJECT_DICT])
        res = ProjectsResource(mock_client)

        projects = res.list_sync()

        assert len(projects) == 1
        assert isinstance(projects[0], Project)


class TestProjectsCreate:
    @pytest.mark.asyncio
    async def test_create_async(self, mock_client):
        mock_client.post = AsyncMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        p = await res.create(name="My Project")

        assert isinstance(p, Project)
        assert p.id == "proj_001"
        assert p.name == "My Project"
        mock_client.post.assert_called_once_with(
            "/api/v1/projects", {"name": "My Project"}
        )

    def test_create_sync(self, mock_client):
        mock_client.post_sync = MagicMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        p = res.create_sync(name="Proj")

        assert isinstance(p, Project)

    @pytest.mark.asyncio
    async def test_create_without_name(self, mock_client):
        mock_client.post = AsyncMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        await res.create()

        mock_client.post.assert_called_once_with("/api/v1/projects", {})


class TestProjectsUpdate:
    @pytest.mark.asyncio
    async def test_update_async(self, mock_client):
        mock_client.put = AsyncMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        p = await res.update("proj_001", name="Renamed", enabled=False)

        assert isinstance(p, Project)
        mock_client.put.assert_called_once_with(
            "/api/v1/projects/proj_001",
            {"name": "Renamed", "enabled": False},
        )

    def test_update_sync(self, mock_client):
        mock_client.put_sync = MagicMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        p = res.update_sync("proj_001", name="New Name")

        assert isinstance(p, Project)
        mock_client.put_sync.assert_called_once_with(
            "/api/v1/projects/proj_001", {"name": "New Name"}
        )

    def test_update_sync_with_enabled(self, mock_client):
        """L417: update_sync with enabled param."""
        mock_client.put_sync = MagicMock(return_value=PROJECT_DICT)
        res = ProjectsResource(mock_client)

        res.update_sync("proj_001", enabled=False)

        body = mock_client.put_sync.call_args[0][1]
        assert body == {"enabled": False}


class TestProjectsDelete:
    @pytest.mark.asyncio
    async def test_delete_async(self, mock_client):
        mock_client.delete = AsyncMock(return_value={})
        res = ProjectsResource(mock_client)

        await res.delete("proj_001")

        mock_client.delete.assert_called_once_with("/api/v1/projects/proj_001")

    def test_delete_sync(self, mock_client):
        mock_client.delete_sync = MagicMock(return_value={})
        res = ProjectsResource(mock_client)

        res.delete_sync("proj_001")

        mock_client.delete_sync.assert_called_once_with("/api/v1/projects/proj_001")


# --------------------------------------------------------------------------- #
#  ProjectSecretsResource
# --------------------------------------------------------------------------- #

class TestProjectSecretsList:
    @pytest.mark.asyncio
    async def test_list_async(self, mock_client):
        mock_client.get = AsyncMock(return_value=[SECRET_DICT])
        res = ProjectSecretsResource(mock_client)

        secrets = await res.list("proj_001")

        assert len(secrets) == 1
        assert isinstance(secrets[0], Secret)
        assert secrets[0].id == "sec_001"
        mock_client.get.assert_called_once_with("/api/v1/projects/proj_001/secrets")

    def test_list_sync(self, mock_client):
        mock_client.get_sync = MagicMock(return_value=[SECRET_DICT])
        res = ProjectSecretsResource(mock_client)

        secrets = res.list_sync("proj_001")

        assert len(secrets) == 1
        assert isinstance(secrets[0], Secret)


class TestProjectSecretsCreate:
    @pytest.mark.asyncio
    async def test_create_async(self, mock_client):
        mock_client.post = AsyncMock(return_value=SECRET_DICT)
        res = ProjectSecretsResource(mock_client)

        s = await res.create("proj_001", "API_KEY", "secret_val")

        assert isinstance(s, Secret)
        assert s.name == "OPENAI_API_KEY"
        mock_client.post.assert_called_once_with(
            "/api/v1/projects/proj_001/secrets",
            {"name": "API_KEY", "value": "secret_val"},
        )

    def test_create_sync(self, mock_client):
        mock_client.post_sync = MagicMock(return_value=SECRET_DICT)
        res = ProjectSecretsResource(mock_client)

        s = res.create_sync("proj_001", "KEY", "val")

        assert isinstance(s, Secret)


class TestProjectSecretsDelete:
    @pytest.mark.asyncio
    async def test_delete_async(self, mock_client):
        mock_client.delete = AsyncMock(return_value={})
        res = ProjectSecretsResource(mock_client)

        await res.delete("proj_001", "sec_001")

        mock_client.delete.assert_called_once_with(
            "/api/v1/projects/proj_001/secrets/sec_001"
        )

    def test_delete_sync(self, mock_client):
        mock_client.delete_sync = MagicMock(return_value={})
        res = ProjectSecretsResource(mock_client)

        res.delete_sync("proj_001", "sec_001")

        mock_client.delete_sync.assert_called_once_with(
            "/api/v1/projects/proj_001/secrets/sec_001"
        )


# --------------------------------------------------------------------------- #
#  Secrets sub-resource on WorkflowsResource and ProjectsResource
# --------------------------------------------------------------------------- #

class TestSecretsSubResource:
    def test_workflows_has_secrets(self, mock_client):
        res = WorkflowsResource(mock_client)
        assert isinstance(res.secrets, WorkflowSecretsResource)

    def test_projects_has_secrets(self, mock_client):
        res = ProjectsResource(mock_client)
        assert isinstance(res.secrets, ProjectSecretsResource)
