"""LangGraph workflow definition for DeepVerify Phase 2."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.core.config import create_search_provider
from app.graph.nodes.document_researcher import document_researcher_node
from app.graph.nodes.planner import make_planner_node
from app.graph.nodes.web_researcher import make_web_researcher_node
from app.graph.nodes.fact_checker import fact_checker_node
from app.graph.nodes.claim_extractor import claim_extractor_node
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider


def build_research_graph(
    llm: LLMProvider,
    search: SearchProvider | None = None,
):
    """Build the Phase 2 research graph with injected providers."""

    search_provider = search or create_search_provider()

    builder = StateGraph(DeepVerifyGraphState)

    builder.add_node("planner", make_planner_node(llm))
    builder.add_node(
        "web_researcher",
        make_web_researcher_node(search_provider),
    )
    builder.add_node(
        "document_researcher",
        document_researcher_node,
    )
    builder.add_node("claim_extractor", claim_extractor_node)
    builder.add_node("fact_checker", fact_checker_node)

    builder.add_edge(START, "planner")

    # Fan-out: both research nodes run in parallel after planning.
    builder.add_edge("planner", "web_researcher")
    builder.add_edge("planner", "document_researcher")

    # Fan-in: graph completes once both branches finish.
    builder.add_edge("web_researcher", "fact_checker")
    builder.add_edge("document_researcher", "fact_checker")
    builder.add_edge("fact_checker", END)

    return builder.compile()