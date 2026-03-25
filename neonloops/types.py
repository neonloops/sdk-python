"""Type definitions for the Neonloops SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class RunInput(BaseModel):
    """Input message for a workflow run."""

    role: Literal["user", "assistant"]
    content: str


class TokenUsage(BaseModel):
    """Token usage information."""

    input: int = 0
    output: int = 0


class RunMetadata(BaseModel):
    """Metadata returned with a run result."""

    provider: Optional[str] = None
    model: Optional[str] = None
    tokens: Optional[TokenUsage] = None
    duration_ms: int = Field(alias="durationMs", default=0)
    nodes_executed: List[str] = Field(alias="nodesExecuted", default_factory=list)

    model_config = {"populate_by_name": True}


class RunResult(BaseModel):
    """Result of a workflow run."""

    id: str
    workflow_id: str
    status: Literal["completed", "failed", "pending_approval"]
    output: Optional[str] = None
    error: Optional[str] = None
    approval_prompt: Optional[str] = None
    paused_at_node_id: Optional[str] = None
    metadata: RunMetadata


class RunOptions(BaseModel):
    """Options for a single workflow run."""

    input: List[RunInput]
    session_id: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    version: Optional[int] = None


# --------------------------------------------------------------------------- #
#  Streaming event types (SSE from /api/v1/run/stream)                        #
# --------------------------------------------------------------------------- #


class StreamEvent(BaseModel):
    """Base stream event — use type field to discriminate."""

    type: str
    model_config = {"extra": "allow"}


class RunStartEvent(BaseModel):
    type: Literal["run:start"]
    run_id: str = Field(alias="runId")
    total_nodes: int = Field(alias="totalNodes")
    model_config = {"populate_by_name": True}


class NodeStartEvent(BaseModel):
    type: Literal["node:start"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    node_label: str = Field(alias="nodeLabel")
    model_config = {"populate_by_name": True}


class NodeCompleteEvent(BaseModel):
    type: Literal["node:complete"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    node_label: str = Field(alias="nodeLabel")
    duration_ms: int = Field(alias="durationMs")
    output_preview: str = Field(alias="outputPreview")
    token_usage: Optional[TokenUsage] = Field(alias="tokenUsage", default=None)
    model_config = {"populate_by_name": True}


class NodeErrorEvent(BaseModel):
    type: Literal["node:error"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    node_label: str = Field(alias="nodeLabel")
    error: str
    model_config = {"populate_by_name": True}


class NodeTextDeltaEvent(BaseModel):
    """Real-time LLM text token from an Agent node."""
    type: Literal["node:text-delta"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    node_label: str = Field(alias="nodeLabel")
    delta: str
    model_config = {"populate_by_name": True}


class EdgeTraversedEvent(BaseModel):
    type: Literal["edge:traversed"]
    run_id: str = Field(alias="runId")
    edge_id: str = Field(alias="edgeId")
    source: str
    target: str
    model_config = {"populate_by_name": True}


class NodeWaitingApprovalEvent(BaseModel):
    type: Literal["node:waiting_approval"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    node_type: str = Field(alias="nodeType")
    node_label: str = Field(alias="nodeLabel")
    approval_prompt: str = Field(alias="approvalPrompt")
    model_config = {"populate_by_name": True}


class RunPausedEvent(BaseModel):
    type: Literal["run:paused"]
    run_id: str = Field(alias="runId")
    paused_at_node_id: str = Field(alias="pausedAtNodeId")
    duration_ms: int = Field(alias="durationMs")
    model_config = {"populate_by_name": True}


class RunResumedEvent(BaseModel):
    type: Literal["run:resumed"]
    run_id: str = Field(alias="runId")
    model_config = {"populate_by_name": True}


class FanOutEvent(BaseModel):
    type: Literal["fan-out"]
    run_id: str = Field(alias="runId")
    source_node_id: str = Field(alias="sourceNodeId")
    target_count: int = Field(alias="targetCount")
    model_config = {"populate_by_name": True}


class FanInWaitingEvent(BaseModel):
    type: Literal["fan-in:waiting"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    arrived: int
    expected: int
    model_config = {"populate_by_name": True}


class FanInReadyEvent(BaseModel):
    type: Literal["fan-in:ready"]
    run_id: str = Field(alias="runId")
    node_id: str = Field(alias="nodeId")
    model_config = {"populate_by_name": True}


class RunCompleteEvent(BaseModel):
    type: Literal["run:complete"]
    run_id: str = Field(alias="runId")
    status: Literal["completed", "failed"]
    duration_ms: int = Field(alias="durationMs")
    error: Optional[str] = None
    model_config = {"populate_by_name": True}


class RunResultEvent(BaseModel):
    type: Literal["run:result"]
    id: str
    workflow_id: str
    status: Literal["completed", "failed", "pending_approval"]
    output: Optional[str] = None
    error: Optional[str] = None
    approval_prompt: Optional[str] = None
    paused_at_node_id: Optional[str] = None
    metadata: RunMetadata


# --------------------------------------------------------------------------- #
#  Resource types (from v1 API)                                                #
# --------------------------------------------------------------------------- #


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    limit: Optional[int] = None
    offset: Optional[int] = None


class Workflow(BaseModel):
    """Workflow summary (list endpoint — no nodes/edges)."""

    id: str
    project_id: str
    name: str
    description: str
    version: int
    status: str
    created_at: str
    updated_at: str


class WorkflowDetail(Workflow):
    """Workflow detail (includes nodes/edges)."""

    nodes: Any = None
    edges: Any = None
    settings: Any = None


class WorkflowRun(BaseModel):
    """Workflow run summary."""

    id: str
    workflow_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    approval_prompt: Optional[str] = None
    paused_at_node_id: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    created_at: str


class WorkflowRunDetail(WorkflowRun):
    """Workflow run detail (includes nodeTrace)."""

    workflow_version: int = 0
    input: Any = None
    metadata: Any = None
    node_trace: Any = None


class Project(BaseModel):
    """Project."""

    id: str
    name: str
    enabled: bool
    created_at: str
    updated_at: str


class Secret(BaseModel):
    """Secret (never includes decrypted value)."""

    id: str
    name: str
    created_at: Optional[str] = None


class WorkflowVersion(BaseModel):
    """Workflow version snapshot."""

    id: str
    workflow_id: str
    version: int
    published_at: str


class WorkflowVersionDetail(WorkflowVersion):
    """Workflow version detail (includes nodes/edges)."""

    nodes: Any = None
    edges: Any = None


class RollbackResult(BaseModel):
    """Result of rolling back a workflow."""

    version: int
    status: str
    rolled_back_from: int


class PublishResult(BaseModel):
    """Result of publishing a workflow."""

    version: int
    status: str


class Session(BaseModel):
    """Chat session for multi-turn conversations."""

    id: str
    workflow_id: str
    title: str
    created_at: str
    updated_at: Optional[str] = None


class SessionMessage(BaseModel):
    """Chat session message."""

    id: str
    session_id: str
    role: str
    content: str
    type: str = "text"
    created_at: str


StreamEventUnion = Union[
    RunStartEvent,
    NodeStartEvent,
    NodeCompleteEvent,
    NodeErrorEvent,
    NodeTextDeltaEvent,
    NodeWaitingApprovalEvent,
    EdgeTraversedEvent,
    FanOutEvent,
    FanInWaitingEvent,
    FanInReadyEvent,
    RunPausedEvent,
    RunResumedEvent,
    RunCompleteEvent,
    RunResultEvent,
]

_EVENT_TYPE_MAP: Dict[str, type] = {
    "run:start": RunStartEvent,
    "node:start": NodeStartEvent,
    "node:complete": NodeCompleteEvent,
    "node:error": NodeErrorEvent,
    "node:text-delta": NodeTextDeltaEvent,
    "node:waiting_approval": NodeWaitingApprovalEvent,
    "edge:traversed": EdgeTraversedEvent,
    "fan-out": FanOutEvent,
    "fan-in:waiting": FanInWaitingEvent,
    "fan-in:ready": FanInReadyEvent,
    "run:paused": RunPausedEvent,
    "run:resumed": RunResumedEvent,
    "run:complete": RunCompleteEvent,
    "run:result": RunResultEvent,
}


def parse_stream_event(data: Dict[str, Any]) -> StreamEventUnion:
    """Parse a raw SSE data dict into the appropriate event model."""
    event_type = data.get("type", "")
    model_cls = _EVENT_TYPE_MAP.get(event_type)
    if model_cls is not None:
        return model_cls(**data)  # type: ignore[return-value]
    return StreamEvent(**data)  # type: ignore[return-value]
