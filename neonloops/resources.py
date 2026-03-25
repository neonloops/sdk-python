"""Resource classes for the Neonloops v1 API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from neonloops.client import NeonloopsClient
from neonloops.types import (
    Workflow,
    WorkflowDetail,
    WorkflowRun,
    WorkflowRunDetail,
    WorkflowVersion,
    WorkflowVersionDetail,
    RollbackResult,
    PublishResult,
    Project,
    Secret,
)


# ---------------------------------------------------------------------------
# WorkflowsResource
# ---------------------------------------------------------------------------


class WorkflowSecretsResource:
    """Manage workflow-level secrets."""

    def __init__(self, client: NeonloopsClient) -> None:
        self._client = client

    async def list(self, workflow_id: str) -> List[Secret]:
        raw = await self._client.get(f"/api/v1/workflows/{workflow_id}/secrets")
        return [Secret(**s) for s in raw]

    def list_sync(self, workflow_id: str) -> List[Secret]:
        raw = self._client.get_sync(f"/api/v1/workflows/{workflow_id}/secrets")
        return [Secret(**s) for s in raw]

    async def create(
        self, workflow_id: str, name: str, value: str
    ) -> Secret:
        raw = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/secrets",
            {"name": name, "value": value},
        )
        return Secret(**raw)

    def create_sync(
        self, workflow_id: str, name: str, value: str
    ) -> Secret:
        raw = self._client.post_sync(
            f"/api/v1/workflows/{workflow_id}/secrets",
            {"name": name, "value": value},
        )
        return Secret(**raw)

    async def delete(self, workflow_id: str, secret_id: str) -> None:
        await self._client.delete(
            f"/api/v1/workflows/{workflow_id}/secrets/{secret_id}"
        )

    def delete_sync(self, workflow_id: str, secret_id: str) -> None:
        self._client.delete_sync(
            f"/api/v1/workflows/{workflow_id}/secrets/{secret_id}"
        )


class WorkflowsResource:
    """Manage workflows, runs, versions, and secrets."""

    def __init__(self, client: NeonloopsClient) -> None:
        self._client = client
        self.secrets = WorkflowSecretsResource(client)

    # -- List --

    async def list(
        self,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Workflow]:
        params: Dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        raw = await self._client.get("/api/v1/workflows", params=params or None)
        return [Workflow(**w) for w in raw]

    def list_sync(
        self,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Workflow]:
        params: Dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        raw = self._client.get_sync("/api/v1/workflows", params=params or None)
        return [Workflow(**w) for w in raw]

    # -- Get --

    async def get(self, workflow_id: str) -> WorkflowDetail:
        raw = await self._client.get(f"/api/v1/workflows/{workflow_id}")
        return WorkflowDetail(**raw)

    def get_sync(self, workflow_id: str) -> WorkflowDetail:
        raw = self._client.get_sync(f"/api/v1/workflows/{workflow_id}")
        return WorkflowDetail(**raw)

    # -- Create --

    async def create(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        nodes: Optional[Any] = None,
        edges: Optional[Any] = None,
    ) -> WorkflowDetail:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["projectId"] = project_id
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        raw = await self._client.post("/api/v1/workflows", body)
        return WorkflowDetail(**raw)

    def create_sync(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        nodes: Optional[Any] = None,
        edges: Optional[Any] = None,
    ) -> WorkflowDetail:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if project_id is not None:
            body["projectId"] = project_id
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        raw = self._client.post_sync("/api/v1/workflows", body)
        return WorkflowDetail(**raw)

    # -- Update --

    async def update(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[str] = None,
        edges: Optional[str] = None,
        settings: Optional[str] = None,
    ) -> WorkflowDetail:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        if settings is not None:
            body["settings"] = settings
        raw = await self._client.put(f"/api/v1/workflows/{workflow_id}", body)
        return WorkflowDetail(**raw)

    def update_sync(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[str] = None,
        edges: Optional[str] = None,
        settings: Optional[str] = None,
    ) -> WorkflowDetail:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        if settings is not None:
            body["settings"] = settings
        raw = self._client.put_sync(f"/api/v1/workflows/{workflow_id}", body)
        return WorkflowDetail(**raw)

    # -- Delete --

    async def delete(self, workflow_id: str) -> None:
        await self._client.delete(f"/api/v1/workflows/{workflow_id}")

    def delete_sync(self, workflow_id: str) -> None:
        self._client.delete_sync(f"/api/v1/workflows/{workflow_id}")

    # -- Publish --

    async def publish(
        self,
        workflow_id: str,
        nodes: Optional[str] = None,
        edges: Optional[str] = None,
    ) -> PublishResult:
        body: Dict[str, Any] = {}
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        raw = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/publish", body
        )
        return PublishResult(**raw)

    def publish_sync(
        self,
        workflow_id: str,
        nodes: Optional[str] = None,
        edges: Optional[str] = None,
    ) -> PublishResult:
        body: Dict[str, Any] = {}
        if nodes is not None:
            body["nodes"] = nodes
        if edges is not None:
            body["edges"] = edges
        raw = self._client.post_sync(
            f"/api/v1/workflows/{workflow_id}/publish", body
        )
        return PublishResult(**raw)

    # -- Versions --

    async def list_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        raw = await self._client.get(f"/api/v1/workflows/{workflow_id}/versions")
        return [WorkflowVersion(**v) for v in raw]

    def list_versions_sync(self, workflow_id: str) -> List[WorkflowVersion]:
        raw = self._client.get_sync(f"/api/v1/workflows/{workflow_id}/versions")
        return [WorkflowVersion(**v) for v in raw]

    async def get_version(self, workflow_id: str, version: int) -> WorkflowVersionDetail:
        raw = await self._client.get(f"/api/v1/workflows/{workflow_id}/versions/{version}")
        return WorkflowVersionDetail(**raw)

    def get_version_sync(self, workflow_id: str, version: int) -> WorkflowVersionDetail:
        raw = self._client.get_sync(f"/api/v1/workflows/{workflow_id}/versions/{version}")
        return WorkflowVersionDetail(**raw)

    async def rollback(self, workflow_id: str, version: int) -> RollbackResult:
        raw = await self._client.post(
            f"/api/v1/workflows/{workflow_id}/rollback",
            {"version": version},
        )
        return RollbackResult(**raw)

    def rollback_sync(self, workflow_id: str, version: int) -> RollbackResult:
        raw = self._client.post_sync(
            f"/api/v1/workflows/{workflow_id}/rollback",
            {"version": version},
        )
        return RollbackResult(**raw)

    # -- Runs --

    async def list_runs(
        self,
        workflow_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[WorkflowRun]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        raw = await self._client.get(
            f"/api/v1/workflows/{workflow_id}/runs", params=params or None
        )
        return [WorkflowRun(**r) for r in raw]

    def list_runs_sync(
        self,
        workflow_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[WorkflowRun]:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        raw = self._client.get_sync(
            f"/api/v1/workflows/{workflow_id}/runs", params=params or None
        )
        return [WorkflowRun(**r) for r in raw]

    async def get_run(
        self, workflow_id: str, run_id: str
    ) -> WorkflowRunDetail:
        raw = await self._client.get(
            f"/api/v1/workflows/{workflow_id}/runs/{run_id}"
        )
        return WorkflowRunDetail(**raw)

    def get_run_sync(
        self, workflow_id: str, run_id: str
    ) -> WorkflowRunDetail:
        raw = self._client.get_sync(
            f"/api/v1/workflows/{workflow_id}/runs/{run_id}"
        )
        return WorkflowRunDetail(**raw)


# ---------------------------------------------------------------------------
# ProjectsResource
# ---------------------------------------------------------------------------


class ProjectSecretsResource:
    """Manage project-level secrets."""

    def __init__(self, client: NeonloopsClient) -> None:
        self._client = client

    async def list(self, project_id: str) -> List[Secret]:
        raw = await self._client.get(f"/api/v1/projects/{project_id}/secrets")
        return [Secret(**s) for s in raw]

    def list_sync(self, project_id: str) -> List[Secret]:
        raw = self._client.get_sync(f"/api/v1/projects/{project_id}/secrets")
        return [Secret(**s) for s in raw]

    async def create(
        self, project_id: str, name: str, value: str
    ) -> Secret:
        raw = await self._client.post(
            f"/api/v1/projects/{project_id}/secrets",
            {"name": name, "value": value},
        )
        return Secret(**raw)

    def create_sync(
        self, project_id: str, name: str, value: str
    ) -> Secret:
        raw = self._client.post_sync(
            f"/api/v1/projects/{project_id}/secrets",
            {"name": name, "value": value},
        )
        return Secret(**raw)

    async def delete(self, project_id: str, secret_id: str) -> None:
        await self._client.delete(
            f"/api/v1/projects/{project_id}/secrets/{secret_id}"
        )

    def delete_sync(self, project_id: str, secret_id: str) -> None:
        self._client.delete_sync(
            f"/api/v1/projects/{project_id}/secrets/{secret_id}"
        )


class ProjectsResource:
    """Manage projects and project-level secrets."""

    def __init__(self, client: NeonloopsClient) -> None:
        self._client = client
        self.secrets = ProjectSecretsResource(client)

    async def list(self) -> List[Project]:
        raw = await self._client.get("/api/v1/projects")
        return [Project(**p) for p in raw]

    def list_sync(self) -> List[Project]:
        raw = self._client.get_sync("/api/v1/projects")
        return [Project(**p) for p in raw]

    async def create(self, name: Optional[str] = None) -> Project:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        raw = await self._client.post("/api/v1/projects", body)
        return Project(**raw)

    def create_sync(self, name: Optional[str] = None) -> Project:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        raw = self._client.post_sync("/api/v1/projects", body)
        return Project(**raw)

    async def update(
        self,
        project_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Project:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if enabled is not None:
            body["enabled"] = enabled
        raw = await self._client.put(f"/api/v1/projects/{project_id}", body)
        return Project(**raw)

    def update_sync(
        self,
        project_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Project:
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if enabled is not None:
            body["enabled"] = enabled
        raw = self._client.put_sync(f"/api/v1/projects/{project_id}", body)
        return Project(**raw)

    async def delete(self, project_id: str) -> None:
        await self._client.delete(f"/api/v1/projects/{project_id}")

    def delete_sync(self, project_id: str) -> None:
        self._client.delete_sync(f"/api/v1/projects/{project_id}")
