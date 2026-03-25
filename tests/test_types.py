"""Tests for neonloops.types — Pydantic models and parse_stream_event."""

import pytest
from pydantic import ValidationError

from neonloops.types import (
    RunInput,
    TokenUsage,
    RunMetadata,
    RunResult,
    RunOptions,
    StreamEvent,
    RunStartEvent,
    NodeStartEvent,
    NodeCompleteEvent,
    NodeErrorEvent,
    NodeWaitingApprovalEvent,
    EdgeTraversedEvent,
    FanOutEvent,
    FanInWaitingEvent,
    FanInReadyEvent,
    RunPausedEvent,
    RunResumedEvent,
    RunCompleteEvent,
    RunResultEvent,
    Workflow,
    WorkflowDetail,
    WorkflowRun,
    WorkflowRunDetail,
    Project,
    Secret,
    WorkflowVersion,
    PublishResult,
    PaginationParams,
    parse_stream_event,
)


# --------------------------------------------------------------------------- #
#  RunInput
# --------------------------------------------------------------------------- #

class TestRunInput:
    def test_valid_user_role(self):
        inp = RunInput(role="user", content="Hello")
        assert inp.role == "user"
        assert inp.content == "Hello"

    def test_valid_assistant_role(self):
        inp = RunInput(role="assistant", content="Hi there")
        assert inp.role == "assistant"
        assert inp.content == "Hi there"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            RunInput(role="system", content="Nope")

    def test_model_dump(self):
        inp = RunInput(role="user", content="Test")
        d = inp.model_dump()
        assert d == {"role": "user", "content": "Test"}


# --------------------------------------------------------------------------- #
#  TokenUsage
# --------------------------------------------------------------------------- #

class TestTokenUsage:
    def test_defaults_to_zero(self):
        t = TokenUsage()
        assert t.input == 0
        assert t.output == 0

    def test_explicit_values(self):
        t = TokenUsage(input=100, output=50)
        assert t.input == 100
        assert t.output == 50


# --------------------------------------------------------------------------- #
#  RunMetadata
# --------------------------------------------------------------------------- #

class TestRunMetadata:
    def test_alias_mapping(self):
        m = RunMetadata(durationMs=1500, nodesExecuted=["n1", "n2"])
        assert m.duration_ms == 1500
        assert m.nodes_executed == ["n1", "n2"]

    def test_populate_by_name(self):
        m = RunMetadata(duration_ms=500, nodes_executed=["n1"])
        assert m.duration_ms == 500
        assert m.nodes_executed == ["n1"]

    def test_defaults(self):
        m = RunMetadata()
        assert m.provider is None
        assert m.model is None
        assert m.tokens is None
        assert m.duration_ms == 0
        assert m.nodes_executed == []

    def test_with_tokens(self):
        m = RunMetadata(
            provider="anthropic",
            model="claude-3",
            tokens=TokenUsage(input=10, output=20),
            durationMs=100,
            nodesExecuted=["n1"],
        )
        assert m.provider == "anthropic"
        assert m.model == "claude-3"
        assert m.tokens.input == 10
        assert m.tokens.output == 20

    def test_from_api_dict(self):
        data = {
            "provider": "openai",
            "model": "gpt-4",
            "tokens": {"input": 200, "output": 100},
            "durationMs": 2000,
            "nodesExecuted": ["a", "b", "c"],
        }
        m = RunMetadata(**data)
        assert m.provider == "openai"
        assert m.model == "gpt-4"
        assert m.tokens.input == 200
        assert m.tokens.output == 100
        assert m.duration_ms == 2000
        assert m.nodes_executed == ["a", "b", "c"]


# --------------------------------------------------------------------------- #
#  RunResult
# --------------------------------------------------------------------------- #

class TestRunResult:
    def test_full_response(self):
        data = {
            "id": "run_123",
            "workflow_id": "wf_abc",
            "status": "completed",
            "output": "Result text",
            "error": None,
            "approval_prompt": None,
            "paused_at_node_id": None,
            "metadata": {
                "provider": "anthropic",
                "model": "claude-3",
                "tokens": {"input": 50, "output": 25},
                "durationMs": 800,
                "nodesExecuted": ["n1"],
            },
        }
        r = RunResult(**data)
        assert r.id == "run_123"
        assert r.workflow_id == "wf_abc"
        assert r.status == "completed"
        assert r.output == "Result text"
        assert r.error is None
        assert r.approval_prompt is None
        assert r.paused_at_node_id is None
        assert r.metadata.provider == "anthropic"
        assert r.metadata.model == "claude-3"
        assert r.metadata.tokens.input == 50
        assert r.metadata.duration_ms == 800
        assert r.metadata.nodes_executed == ["n1"]

    def test_minimal_response(self):
        data = {
            "id": "run_min",
            "workflow_id": "wf_min",
            "status": "failed",
            "metadata": {},
        }
        r = RunResult(**data)
        assert r.id == "run_min"
        assert r.workflow_id == "wf_min"
        assert r.status == "failed"
        assert r.output is None
        assert r.error is None
        assert r.metadata.duration_ms == 0

    def test_pending_approval_status(self):
        data = {
            "id": "run_pa",
            "workflow_id": "wf_pa",
            "status": "pending_approval",
            "approval_prompt": "Approve?",
            "paused_at_node_id": "n5",
            "metadata": {"durationMs": 100, "nodesExecuted": ["n1"]},
        }
        r = RunResult(**data)
        assert r.status == "pending_approval"
        assert r.approval_prompt == "Approve?"
        assert r.paused_at_node_id == "n5"


# --------------------------------------------------------------------------- #
#  RunOptions
# --------------------------------------------------------------------------- #

class TestRunOptions:
    def test_construction(self):
        opts = RunOptions(input=[RunInput(role="user", content="hi")])
        assert len(opts.input) == 1
        assert opts.session_id is None
        assert opts.variables is None

    def test_with_all_fields(self):
        opts = RunOptions(
            input=[RunInput(role="user", content="hi")],
            session_id="sess_1",
            variables={"key": "value"},
        )
        assert opts.session_id == "sess_1"
        assert opts.variables == {"key": "value"}


# --------------------------------------------------------------------------- #
#  Stream events
# --------------------------------------------------------------------------- #

class TestRunStartEvent:
    def test_from_camel_case(self):
        e = RunStartEvent(type="run:start", runId="run_1", totalNodes=5)
        assert e.type == "run:start"
        assert e.run_id == "run_1"
        assert e.total_nodes == 5

    def test_from_snake_case(self):
        e = RunStartEvent(type="run:start", run_id="run_1", total_nodes=3)
        assert e.run_id == "run_1"
        assert e.total_nodes == 3


class TestNodeStartEvent:
    def test_from_camel_case(self):
        e = NodeStartEvent(
            type="node:start",
            runId="run_1",
            nodeId="n1",
            nodeType="prompt",
            nodeLabel="My Prompt",
        )
        assert e.run_id == "run_1"
        assert e.node_id == "n1"
        assert e.node_type == "prompt"
        assert e.node_label == "My Prompt"


class TestNodeCompleteEvent:
    def test_from_camel_case(self):
        e = NodeCompleteEvent(
            type="node:complete",
            runId="run_1",
            nodeId="n1",
            nodeType="prompt",
            nodeLabel="P",
            durationMs=100,
            outputPreview="Hello...",
            tokenUsage={"input": 10, "output": 5},
        )
        assert e.run_id == "run_1"
        assert e.node_id == "n1"
        assert e.duration_ms == 100
        assert e.output_preview == "Hello..."
        assert e.token_usage.input == 10
        assert e.token_usage.output == 5

    def test_without_token_usage(self):
        e = NodeCompleteEvent(
            type="node:complete",
            runId="run_1",
            nodeId="n1",
            nodeType="condition",
            nodeLabel="Check",
            durationMs=5,
            outputPreview="true",
        )
        assert e.token_usage is None


class TestNodeErrorEvent:
    def test_from_camel_case(self):
        e = NodeErrorEvent(
            type="node:error",
            runId="run_1",
            nodeId="n1",
            nodeType="prompt",
            nodeLabel="P",
            error="Model failed",
        )
        assert e.error == "Model failed"
        assert e.run_id == "run_1"
        assert e.node_id == "n1"


class TestEdgeTraversedEvent:
    def test_from_camel_case(self):
        e = EdgeTraversedEvent(
            type="edge:traversed",
            runId="run_1",
            edgeId="e1",
            source="n1",
            target="n2",
        )
        assert e.edge_id == "e1"
        assert e.source == "n1"
        assert e.target == "n2"


class TestNodeWaitingApprovalEvent:
    def test_from_camel_case(self):
        e = NodeWaitingApprovalEvent(
            type="node:waiting_approval",
            runId="run_1",
            nodeId="n1",
            nodeType="approval",
            nodeLabel="Approve",
            approvalPrompt="OK?",
        )
        assert e.approval_prompt == "OK?"


class TestRunPausedEvent:
    def test_from_camel_case(self):
        e = RunPausedEvent(
            type="run:paused",
            runId="run_1",
            pausedAtNodeId="n3",
            durationMs=500,
        )
        assert e.paused_at_node_id == "n3"
        assert e.duration_ms == 500


class TestRunResumedEvent:
    def test_from_camel_case(self):
        e = RunResumedEvent(type="run:resumed", runId="run_1")
        assert e.run_id == "run_1"


class TestFanOutEvent:
    def test_from_camel_case(self):
        e = FanOutEvent(
            type="fan-out",
            runId="run_1",
            sourceNodeId="n1",
            targetCount=3,
        )
        assert e.source_node_id == "n1"
        assert e.target_count == 3


class TestFanInWaitingEvent:
    def test_from_camel_case(self):
        e = FanInWaitingEvent(
            type="fan-in:waiting",
            runId="run_1",
            nodeId="n5",
            arrived=2,
            expected=3,
        )
        assert e.arrived == 2
        assert e.expected == 3


class TestFanInReadyEvent:
    def test_from_camel_case(self):
        e = FanInReadyEvent(
            type="fan-in:ready",
            runId="run_1",
            nodeId="n5",
        )
        assert e.node_id == "n5"


class TestRunCompleteEvent:
    def test_completed(self):
        e = RunCompleteEvent(
            type="run:complete",
            runId="run_1",
            status="completed",
            durationMs=2000,
        )
        assert e.status == "completed"
        assert e.duration_ms == 2000
        assert e.error is None

    def test_failed_with_error(self):
        e = RunCompleteEvent(
            type="run:complete",
            runId="run_1",
            status="failed",
            durationMs=100,
            error="Something went wrong",
        )
        assert e.status == "failed"
        assert e.error == "Something went wrong"


class TestRunResultEvent:
    def test_from_api_data(self):
        e = RunResultEvent(
            type="run:result",
            id="run_1",
            workflow_id="wf_1",
            status="completed",
            output="Done",
            metadata={
                "durationMs": 100,
                "nodesExecuted": ["n1"],
            },
        )
        assert e.id == "run_1"
        assert e.output == "Done"
        assert e.metadata.duration_ms == 100


# --------------------------------------------------------------------------- #
#  parse_stream_event
# --------------------------------------------------------------------------- #

class TestParseStreamEvent:
    def test_run_start(self):
        e = parse_stream_event({"type": "run:start", "runId": "r1", "totalNodes": 3})
        assert isinstance(e, RunStartEvent)
        assert e.run_id == "r1"

    def test_node_start(self):
        e = parse_stream_event({
            "type": "node:start",
            "runId": "r1",
            "nodeId": "n1",
            "nodeType": "prompt",
            "nodeLabel": "P",
        })
        assert isinstance(e, NodeStartEvent)

    def test_node_complete(self):
        e = parse_stream_event({
            "type": "node:complete",
            "runId": "r1",
            "nodeId": "n1",
            "nodeType": "prompt",
            "nodeLabel": "P",
            "durationMs": 50,
            "outputPreview": "hi",
        })
        assert isinstance(e, NodeCompleteEvent)

    def test_node_error(self):
        e = parse_stream_event({
            "type": "node:error",
            "runId": "r1",
            "nodeId": "n1",
            "nodeType": "prompt",
            "nodeLabel": "P",
            "error": "fail",
        })
        assert isinstance(e, NodeErrorEvent)

    def test_edge_traversed(self):
        e = parse_stream_event({
            "type": "edge:traversed",
            "runId": "r1",
            "edgeId": "e1",
            "source": "n1",
            "target": "n2",
        })
        assert isinstance(e, EdgeTraversedEvent)

    def test_node_waiting_approval(self):
        e = parse_stream_event({
            "type": "node:waiting_approval",
            "runId": "r1",
            "nodeId": "n1",
            "nodeType": "approval",
            "nodeLabel": "A",
            "approvalPrompt": "OK?",
        })
        assert isinstance(e, NodeWaitingApprovalEvent)

    def test_fan_out(self):
        e = parse_stream_event({
            "type": "fan-out",
            "runId": "r1",
            "sourceNodeId": "n1",
            "targetCount": 2,
        })
        assert isinstance(e, FanOutEvent)

    def test_fan_in_waiting(self):
        e = parse_stream_event({
            "type": "fan-in:waiting",
            "runId": "r1",
            "nodeId": "n1",
            "arrived": 1,
            "expected": 3,
        })
        assert isinstance(e, FanInWaitingEvent)

    def test_fan_in_ready(self):
        e = parse_stream_event({
            "type": "fan-in:ready",
            "runId": "r1",
            "nodeId": "n1",
        })
        assert isinstance(e, FanInReadyEvent)

    def test_run_paused(self):
        e = parse_stream_event({
            "type": "run:paused",
            "runId": "r1",
            "pausedAtNodeId": "n3",
            "durationMs": 500,
        })
        assert isinstance(e, RunPausedEvent)

    def test_run_resumed(self):
        e = parse_stream_event({"type": "run:resumed", "runId": "r1"})
        assert isinstance(e, RunResumedEvent)

    def test_run_complete(self):
        e = parse_stream_event({
            "type": "run:complete",
            "runId": "r1",
            "status": "completed",
            "durationMs": 1000,
        })
        assert isinstance(e, RunCompleteEvent)

    def test_run_result(self):
        e = parse_stream_event({
            "type": "run:result",
            "id": "run_1",
            "workflow_id": "wf_1",
            "status": "completed",
            "metadata": {},
        })
        assert isinstance(e, RunResultEvent)

    def test_unknown_type_returns_stream_event(self):
        e = parse_stream_event({"type": "unknown:event", "foo": "bar"})
        assert isinstance(e, StreamEvent)
        assert e.type == "unknown:event"

    def test_missing_type_falls_back_to_stream_event(self):
        """When type is present but not in the event map, StreamEvent is returned."""
        e = parse_stream_event({"type": "", "foo": "bar"})
        assert isinstance(e, StreamEvent)
        assert e.type == ""


# --------------------------------------------------------------------------- #
#  Resource types
# --------------------------------------------------------------------------- #

class TestWorkflow:
    def test_from_dict(self):
        w = Workflow(
            id="wf_1",
            project_id="p1",
            name="W",
            description="D",
            version=1,
            status="draft",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert w.id == "wf_1"
        assert w.project_id == "p1"
        assert w.name == "W"
        assert w.description == "D"
        assert w.version == 1
        assert w.status == "draft"
        assert w.created_at == "2025-01-01T00:00:00Z"
        assert w.updated_at == "2025-01-01T00:00:00Z"


class TestWorkflowDetail:
    def test_inherits_workflow_and_has_extra(self):
        wd = WorkflowDetail(
            id="wf_1",
            project_id="p1",
            name="W",
            description="D",
            version=2,
            status="published",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
            nodes=[{"id": "n1"}],
            edges=[{"id": "e1"}],
            settings={"timeout": 60},
        )
        assert wd.nodes == [{"id": "n1"}]
        assert wd.edges == [{"id": "e1"}]
        assert wd.settings == {"timeout": 60}
        # inherited
        assert wd.id == "wf_1"
        assert wd.version == 2


class TestWorkflowRun:
    def test_from_dict(self):
        wr = WorkflowRun(
            id="run_1",
            workflow_id="wf_1",
            status="completed",
            output="ok",
            started_at="2025-01-01T00:00:00Z",
            created_at="2025-01-01T00:00:00Z",
        )
        assert wr.id == "run_1"
        assert wr.status == "completed"
        assert wr.output == "ok"
        assert wr.error is None
        assert wr.completed_at is None


class TestWorkflowRunDetail:
    def test_inherits_and_has_extra(self):
        wrd = WorkflowRunDetail(
            id="run_1",
            workflow_id="wf_1",
            status="completed",
            started_at="2025-01-01T00:00:00Z",
            created_at="2025-01-01T00:00:00Z",
            workflow_version=3,
            input=[{"role": "user", "content": "hi"}],
            metadata={"provider": "openai"},
            node_trace=[{"nodeId": "n1"}],
        )
        assert wrd.workflow_version == 3
        assert wrd.input == [{"role": "user", "content": "hi"}]
        assert wrd.node_trace == [{"nodeId": "n1"}]


class TestProject:
    def test_from_dict(self):
        p = Project(
            id="p1",
            name="Proj",
            enabled=True,
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert p.id == "p1"
        assert p.name == "Proj"
        assert p.enabled is True


class TestSecret:
    def test_from_dict(self):
        s = Secret(id="s1", name="API_KEY", created_at="2025-01-01T00:00:00Z")
        assert s.id == "s1"
        assert s.name == "API_KEY"


class TestWorkflowVersion:
    def test_from_dict(self):
        v = WorkflowVersion(
            id="v1",
            workflow_id="wf_1",
            version=5,
            published_at="2025-03-01T00:00:00Z",
        )
        assert v.version == 5
        assert v.workflow_id == "wf_1"


class TestPublishResult:
    def test_from_dict(self):
        pr = PublishResult(version=4, status="published")
        assert pr.version == 4
        assert pr.status == "published"


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.limit is None
        assert p.offset is None

    def test_with_values(self):
        p = PaginationParams(limit=10, offset=20)
        assert p.limit == 10
        assert p.offset == 20
