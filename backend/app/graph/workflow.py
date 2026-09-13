"""LangGraph workflow definition for DeepVerify Phase 2."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.core.config import create_search_provider
from app.graph.nodes.document_researcher import document_researcher_node
from app.graph.nodes.planner import make_planner_node
from app.graph.nodes.web_researcher import make_web_researcher_node
from app.graph.nodes.fact_checker import make_fact_checker_node
from app.graph.nodes.claim_extractor import make_claim_extractor_node
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider
from app.graph.nodes.revision_decider import revision_decider_node
from app.graph.nodes.revision_researcher import make_revision_researcher_node
from app.agents.revision_decider import RevisionDecider
from app.core.config import get_settings

def route_revision(state: DeepVerifyGraphState) -> str:
    """Route to targeted research or finish the workflow."""

    settings = get_settings()
    decider = RevisionDecider(settings)

    should_revise = decider.should_revise(
        grounding_score=state.grounding_score,
        revision_count=state.revision_count,
    )

    return "revise" if should_revise else "finish"


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
    
    builder.add_node(
    "claim_extractor",
    make_claim_extractor_node(llm),
    )
    
    builder.add_node("fact_checker", make_fact_checker_node(llm))

    builder.add_node("revision_decider", revision_decider_node)
    builder.add_node(
        "revision_researcher",
        make_revision_researcher_node(search_provider),
    )

    builder.add_edge(START, "planner")

    # Fan-out: both research nodes run in parallel after planning.
    builder.add_edge("planner", "web_researcher")
    builder.add_edge("planner", "document_researcher")

    # Fan-in: graph completes once both branches finish.
    builder.add_edge("web_researcher", "claim_extractor")
    builder.add_edge("document_researcher", "claim_extractor")
    builder.add_edge("claim_extractor", "fact_checker")
    builder.add_edge("fact_checker", "revision_decider")

    builder.add_conditional_edges(
    "revision_decider",
    route_revision,
    {
        "revise": "revision_researcher",
        "finish": END,
    },
    )
    builder.add_edge("revision_researcher", "fact_checker")

    return builder.compile()