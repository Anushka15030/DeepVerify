"""Tests for LangGraph workflow and graph runner."""

from __future__ import annotations

import json

import pytest

from app.graph.workflow import build_research_graph
from app.services.graph_runner import run_research


@pytest.mark.asyncio
async def test_graph_executes_end_to_end() -> None:
    state = await run_research("How does CRISPR gene editing work?")
    assert state.run_id
    assert state.original_question == "How does CRISPR gene editing work?"
    assert state.research_plan is not None
    assert len(state.research_plan.subtasks) == 3
    assert state.errors == []


@pytest.mark.asyncio
async def test_graph_contains_expected_nodes() -> None:
    from app.core.config import create_llm_provider

    graph = build_research_graph(create_llm_provider())
    node_names = set(graph.get_graph().nodes.keys())
    assert "planner" in node_names
    assert "web_researcher" in node_names
    assert "document_researcher" in node_names


@pytest.mark.asyncio
async def test_placeholder_research_nodes_emit_events() -> None:
    state = await run_research("Solar panel efficiency trends")
    agents = {event.payload.get("agent") for event in state.agent_events}
    assert "planner" in agents
    assert "web_researcher" in agents
    assert "document_researcher" in agents

    web_events = [
        e for e in state.agent_events if e.payload.get("agent") == "web_researcher"
    ]
    doc_events = [
        e for e in state.agent_events if e.payload.get("agent") == "document_researcher"
    ]
    assert any(e.type == "search_started" for e in web_events)
    assert any(e.type == "search_completed" for e in web_events)
    assert any(e.payload.get("mode") == "placeholder" for e in web_events)
    assert any(e.type == "search_started" for e in doc_events)
    assert any(e.payload.get("mode") == "placeholder" for e in doc_events)


@pytest.mark.asyncio
async def test_state_preserved_through_workflow() -> None:
    run_id = "test-run-abc123"
    question = "Blockchain scalability solutions"
    state = await run_research(question, run_id=run_id)
    assert state.run_id == run_id
    assert state.original_question == question
    assert state.revision_count == 0
    assert state.grounding_score is None
    assert state.draft is None
    assert state.claims == []
    assert state.claim_checks == []
    assert state.evidence == []


@pytest.mark.asyncio
async def test_run_completed_event_emitted() -> None:
    state = await run_research("Machine learning in healthcare")
    assert any(event.type == "run_completed" for event in state.agent_events)


@pytest.mark.asyncio
async def test_plan_created_event_emitted() -> None:
    state = await run_research("Autonomous vehicle safety")
    plan_events = [e for e in state.agent_events if e.type == "plan_created"]
    assert len(plan_events) == 1
    assert plan_events[0].payload["subtask_count"] == 3


class _InvalidPlanLLM:
    async def complete(self, prompt: str, system: str | None = None) -> str:
        return json.dumps({"subtasks": []})


@pytest.mark.asyncio
async def test_invalid_planner_output_handled() -> None:
    state = await run_research("Bad plan test", llm=_InvalidPlanLLM())
    assert state.research_plan is None
    assert len(state.errors) >= 1
    assert any(event.type == "error" for event in state.agent_events)
    error_events = [e for e in state.agent_events if e.type == "error"]
    assert error_events[0].payload.get("agent") == "planner"
