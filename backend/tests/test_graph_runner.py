"""Tests for LangGraph workflow and graph runner."""

from __future__ import annotations

import json

import pytest

from app.core.models import Evidence, ResearchPlan, ResearchSubtask
from app.graph.nodes.web_researcher import make_web_researcher_node
from app.graph.state import DeepVerifyGraphState
from app.graph.workflow import build_research_graph
from app.providers.search import SearchResponse, SearchResult
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

    agents = {
        event.payload.get("agent")
        for event in state.agent_events
    }

    assert "planner" in agents
    assert "web_researcher" in agents
    assert "document_researcher" in agents

    web_events = [
        event
        for event in state.agent_events
        if event.payload.get("agent") == "web_researcher"
    ]

    doc_events = [
        event
        for event in state.agent_events
        if event.payload.get("agent") == "document_researcher"
    ]

    assert any(
        event.type == "search_started"
        for event in web_events
    )

    assert any(
        event.type == "search_completed"
        for event in web_events
    )

    assert any(
        event.payload.get("mode") == "placeholder"
        for event in web_events
    )

    assert any(
        event.type == "search_started"
        for event in doc_events
    )

    assert any(
        event.payload.get("mode") == "placeholder"
        for event in doc_events
    )


@pytest.mark.asyncio
async def test_state_preserved_through_workflow() -> None:
    run_id = "test-run-abc123"
    question = "Blockchain scalability solutions"

    state = await run_research(
        question,
        run_id=run_id,
    )

    assert state.run_id == run_id
    assert state.original_question == question
    assert state.revision_count == 0
    assert state.grounding_score == 0.0
    assert state.draft is None
    assert state.claims == []
    assert state.claim_checks == []
    assert len(state.evidence) == 3
    assert all(evidence.confidence == 0.5 for evidence in state.evidence)


@pytest.mark.asyncio
async def test_run_completed_event_emitted() -> None:
    state = await run_research("Machine learning in healthcare")

    assert any(
        event.type == "run_completed"
        for event in state.agent_events
    )


@pytest.mark.asyncio
async def test_plan_created_event_emitted() -> None:
    state = await run_research("Autonomous vehicle safety")

    plan_events = [
        event
        for event in state.agent_events
        if event.type == "plan_created"
    ]

    assert len(plan_events) == 1
    assert plan_events[0].payload["subtask_count"] == 3


class _InvalidPlanLLM:
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return json.dumps({"subtasks": []})


@pytest.mark.asyncio
async def test_invalid_planner_output_handled() -> None:
    state = await run_research(
        "Bad plan test",
        llm=_InvalidPlanLLM(),
    )

    assert state.research_plan is None
    assert len(state.errors) >= 1
    assert any(
        event.type == "error"
        for event in state.agent_events
    )

    error_events = [
        event
        for event in state.agent_events
        if event.type == "error"
    ]

    assert error_events[0].payload.get("agent") == "planner"


class _RecordingSearchProvider:
    """Search provider used to verify Web Researcher behavior."""

    provider_name = "recording"

    def __init__(self) -> None:
        self.queries: list[str] = []

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> SearchResponse:
        self.queries.append(query)

        return SearchResponse(
            query=query,
            results=[
                SearchResult(
                    title=f"Result for {query}",
                    url=f"https://example.com/{len(self.queries)}",
                    snippet=f"Snippet for {query}",
                    content=f"Content for {query}",
                    provider=self.provider_name,
                )
            ],
        )


def _make_test_state() -> DeepVerifyGraphState:
    """Create a graph state containing three known research subtasks."""

    plan = ResearchPlan(
        topic="Test research topic",
        subtasks=[
            ResearchSubtask(
                id="subtask-1",
                query="consensus query",
                purpose="consensus",
            ),
            ResearchSubtask(
                id="subtask-2",
                query="empirical query",
                purpose="empirical",
            ),
            ResearchSubtask(
                id="subtask-3",
                query="counterargument query",
                purpose="counterarguments",
            ),
        ],
    )

    return DeepVerifyGraphState(
        run_id="test-web-research-run",
        original_question="Test research topic",
        research_plan=plan,
    )


@pytest.mark.asyncio
async def test_web_researcher_calls_injected_search_provider() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)

    state = _make_test_state()

    result = await node(state)

    assert search.queries == [
        "consensus query",
        "empirical query",
        "counterargument query",
    ]

    assert len(result["agent_events"]) == 2


@pytest.mark.asyncio
async def test_web_researcher_reports_total_result_count() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)

    state = _make_test_state()

    result = await node(state)

    completed_event = next(
        event
        for event in result["agent_events"]
        if event.type == "search_completed"
    )

    assert completed_event.payload["results_count"] == 3
    assert completed_event.payload["subtask_count"] == 3


@pytest.mark.asyncio
async def test_web_researcher_reports_provider_name() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)

    state = _make_test_state()

    result = await node(state)

    for event in result["agent_events"]:
        assert event.payload["provider"] == "_RecordingSearchProvider"


@pytest.mark.asyncio
async def test_web_researcher_handles_missing_plan() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)

    state = DeepVerifyGraphState(
        run_id="test-no-plan",
        original_question="Test without plan",
        research_plan=None,
    )

    result = await node(state)

    assert search.queries == []

    assert len(result["agent_events"]) == 2

    completed_event = next(
        event
        for event in result["agent_events"]
        if event.type == "search_completed"
    )

    assert completed_event.payload["results_count"] == 0

@pytest.mark.asyncio
async def test_web_researcher_returns_evidence_from_search_results() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)
    state = _make_test_state()

    result = await node(state)

    evidence = result["evidence"]

    assert len(evidence) == 3

    for item in evidence:
        assert item.excerpt
        assert item.confidence == 0.5
        assert len(item.sources) == 1
        assert item.sources[0].provider == "recording"
        assert item.sources[0].url.startswith("https://example.com/")


@pytest.mark.asyncio
async def test_web_researcher_prefers_content_over_snippet() -> None:
    search = _RecordingSearchProvider()
    node = make_web_researcher_node(search)
    state = _make_test_state()

    result = await node(state)

    evidence = result["evidence"]

    assert evidence[0].excerpt == "Content for consensus query"


@pytest.mark.asyncio
async def test_web_researcher_falls_back_to_snippet() -> None:
    class _SnippetOnlySearchProvider:
        async def search(
            self,
            query: str,
            *,
            max_results: int = 5,
        ) -> SearchResponse:
            return SearchResponse(
                query=query,
                results=[
                    SearchResult(
                        title="Snippet Result",
                        url="https://example.com/snippet",
                        snippet="Snippet-only evidence",
                        content="",
                        provider="snippet-only",
                    )
                ],
            )

    search = _SnippetOnlySearchProvider()
    node = make_web_researcher_node(search)
    state = _make_test_state()

    result = await node(state)

    evidence = result["evidence"]

    assert len(evidence) == 3
    assert all(
        item.excerpt == "Snippet-only evidence"
        for item in evidence
    )


@pytest.mark.asyncio
async def test_web_researcher_excludes_results_without_text() -> None:
    class _EmptyResultSearchProvider:
        async def search(
            self,
            query: str,
            *,
            max_results: int = 5,
        ) -> SearchResponse:
            return SearchResponse(
                query=query,
                results=[
                    SearchResult(
                        title="Empty Result",
                        url="https://example.com/empty",
                        snippet="",
                        content="",
                        provider="empty",
                    )
                ],
            )

    search = _EmptyResultSearchProvider()
    node = make_web_researcher_node(search)
    state = _make_test_state()

    result = await node(state)

    assert result["evidence"] == []

    completed_event = next(
        event
        for event in result["agent_events"]
        if event.type == "search_completed"
    )

    assert completed_event.payload["results_count"] == 3
    assert completed_event.payload["evidence_count"] == 0


@pytest.mark.asyncio
async def test_graph_runner_populates_evidence() -> None:
    state = await run_research("Solar panel efficiency trends")

    assert len(state.evidence) == 3

    for evidence in state.evidence:
        assert evidence.excerpt
        assert evidence.confidence == 0.5
        assert len(evidence.sources) == 1