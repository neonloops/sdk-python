"""High-level runner for executing Neonloops workflows."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union

from neonloops.client import NeonloopsClient
from neonloops.resources import WorkflowsResource, ProjectsResource
from neonloops.types import RunInput, RunResult, StreamEventUnion, parse_stream_event, Session, SessionMessage

_DEFAULT_BASE_URL = "https://neonloops.com"


class Runner:
    """Execute Neonloops workflows via the API.

    Example::

        from neonloops import Runner, RunInput

        runner = Runner(
            api_key="nl_sk_...",
        )

        result = await runner.run(
            workflow_id="wf_abc123",
            input=[RunInput(role="user", content="Hello!")],
        )
        print(result.output)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        project_id: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 2,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._project_id = project_id
        self._client = NeonloopsClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        self.workflows = WorkflowsResource(self._client)
        self.projects = ProjectsResource(self._client)

    async def run(
        self,
        workflow_id: str,
        input: List[Union[RunInput, Dict[str, str]]],
        variables: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> RunResult:
        """Run a workflow asynchronously.

        Args:
            workflow_id: The workflow ID (e.g. "wf_abc123").
            input: List of input messages.
            variables: Optional variables to pass to the workflow.
            session_id: Optional session ID for multi-turn conversations.
            version: Optional version number to pin execution to a specific published version.

        Returns:
            RunResult with output, status, and metadata.
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")
        if not input:
            raise ValueError("At least one input message is required")

        body = self._build_body(workflow_id, input, variables, session_id, version)
        data = await self._client.post("/api/v1/run", body)
        return RunResult(**data)

    def run_sync(
        self,
        workflow_id: str,
        input: List[Union[RunInput, Dict[str, str]]],
        variables: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> RunResult:
        """Run a workflow synchronously.

        Same as :meth:`run` but uses a synchronous HTTP client.
        Useful in scripts and notebooks that don't use asyncio.
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")
        if not input:
            raise ValueError("At least one input message is required")

        body = self._build_body(workflow_id, input, variables, session_id, version)
        data = self._client.post_sync("/api/v1/run", body)
        return RunResult(**data)

    async def run_stream(
        self,
        workflow_id: str,
        input: List[Union[RunInput, Dict[str, str]]],
        variables: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> AsyncIterator[StreamEventUnion]:
        """Stream workflow execution events asynchronously."""
        if not workflow_id:
            raise ValueError("workflow_id is required")
        if not input:
            raise ValueError("At least one input message is required")

        body = self._build_body(workflow_id, input, variables, session_id, version)
        async for data in self._client.stream("/api/v1/run/stream", body):
            yield parse_stream_event(data)

    def run_stream_sync(
        self,
        workflow_id: str,
        input: List[Union[RunInput, Dict[str, str]]],
        variables: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Iterator[StreamEventUnion]:
        """Stream workflow execution events synchronously."""
        if not workflow_id:
            raise ValueError("workflow_id is required")
        if not input:
            raise ValueError("At least one input message is required")

        body = self._build_body(workflow_id, input, variables, session_id, version)
        for data in self._client.stream_sync("/api/v1/run/stream", body):
            yield parse_stream_event(data)

    async def approve(
        self,
        run_id: str,
        comment: Optional[str] = None,
    ) -> RunResult:
        """Approve a paused workflow run (pending_approval status).

        Args:
            run_id: The run ID (e.g. "run_abc123").
            comment: Optional comment.

        Returns:
            RunResult with the resumed run's output.
        """
        if not run_id:
            raise ValueError("run_id is required")

        body: Dict[str, Any] = {}
        if comment:
            body["comment"] = comment

        data = await self._client.post(f"/api/v1/run/{run_id}/approve", body)
        return RunResult(**data)

    def approve_sync(
        self,
        run_id: str,
        comment: Optional[str] = None,
    ) -> RunResult:
        """Approve a paused workflow run synchronously."""
        if not run_id:
            raise ValueError("run_id is required")

        body: Dict[str, Any] = {}
        if comment:
            body["comment"] = comment

        data = self._client.post_sync(f"/api/v1/run/{run_id}/approve", body)
        return RunResult(**data)

    async def reject(
        self,
        run_id: str,
        comment: Optional[str] = None,
    ) -> RunResult:
        """Reject a paused workflow run (pending_approval status).

        Args:
            run_id: The run ID (e.g. "run_abc123").
            comment: Optional comment.

        Returns:
            RunResult with the rejected run's output.
        """
        if not run_id:
            raise ValueError("run_id is required")

        body: Dict[str, Any] = {}
        if comment:
            body["comment"] = comment

        data = await self._client.post(f"/api/v1/run/{run_id}/reject", body)
        return RunResult(**data)

    def reject_sync(
        self,
        run_id: str,
        comment: Optional[str] = None,
    ) -> RunResult:
        """Reject a paused workflow run synchronously."""
        if not run_id:
            raise ValueError("run_id is required")

        body: Dict[str, Any] = {}
        if comment:
            body["comment"] = comment

        data = self._client.post_sync(f"/api/v1/run/{run_id}/reject", body)
        return RunResult(**data)

    async def create_session(
        self,
        workflow_id: str,
        title: Optional[str] = None,
    ) -> Session:
        """Create a new chat session for multi-turn conversations.

        Args:
            workflow_id: The workflow ID (e.g. "wf_abc123").
            title: Optional session title.

        Returns:
            Session with id, workflow_id, title, and created_at.
        """
        body: Dict[str, Any] = {"workflow_id": workflow_id}
        if title:
            body["title"] = title
        data = await self._client.post("/api/v1/sessions", body)
        return Session(**data)

    def create_session_sync(
        self,
        workflow_id: str,
        title: Optional[str] = None,
    ) -> Session:
        """Create a new chat session synchronously."""
        body: Dict[str, Any] = {"workflow_id": workflow_id}
        if title:
            body["title"] = title
        data = self._client.post_sync("/api/v1/sessions", body)
        return Session(**data)

    async def list_sessions(self, workflow_id: str) -> List[Session]:
        """List chat sessions for a workflow.

        Args:
            workflow_id: The workflow ID.

        Returns:
            List of sessions (newest first).
        """
        res = await self._client.get(
            "/api/v1/sessions", params={"workflow_id": workflow_id}
        )
        return [Session(**s) for s in res["data"]]

    def list_sessions_sync(self, workflow_id: str) -> List[Session]:
        """List chat sessions synchronously."""
        res = self._client.get_sync(
            "/api/v1/sessions", params={"workflow_id": workflow_id}
        )
        return [Session(**s) for s in res["data"]]

    async def get_session_messages(self, session_id: str) -> List[SessionMessage]:
        """Get messages for a chat session.

        Args:
            session_id: The session ID.

        Returns:
            List of messages in chronological order.
        """
        res = await self._client.get(f"/api/v1/sessions/{session_id}/messages")
        return [SessionMessage(**m) for m in res["data"]]

    def get_session_messages_sync(self, session_id: str) -> List[SessionMessage]:
        """Get session messages synchronously."""
        res = self._client.get_sync(f"/api/v1/sessions/{session_id}/messages")
        return [SessionMessage(**m) for m in res["data"]]

    def _build_body(
        self,
        workflow_id: str,
        input: List[Union[RunInput, Dict[str, str]]],
        variables: Optional[Dict[str, Any]],
        session_id: Optional[str],
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        serialized_input = [
            item.model_dump() if isinstance(item, RunInput) else item
            for item in input
        ]

        body: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "input": serialized_input,
        }

        if session_id:
            body["session_id"] = session_id
        if variables:
            body["variables"] = variables
        if version is not None:
            body["version"] = version

        return body
