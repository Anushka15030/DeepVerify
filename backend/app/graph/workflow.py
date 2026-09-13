"""LangGraph workflow definition for DeepVerify Phase 2."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.revision_decider import RevisionDecider
from app.core.config import (
    create_document_retrieval_provider,
    create_search_provider,
    get_settings,
)
from app.graph.nodes.claim_extractor import make_claim_extractor_node
from app.graph.nodes.document_researcher import (
    make_document_researcher_node,
)
from app.graph.nodes.fact_checker import make_fact_checker_node
from app.graph.nodes.planner import make_planner_node
from app.graph.nodes.revision_decider import revision_decider_node
from app.graph.nodes.revision_researcher import (
    make_revision_researcher_node,
)
from app.graph.nodes.writer import make_writer_node
from app.graph.nodes.web_researcher import make_web_researcher_node
from app.graph.state import DeepVerifyGraphState
from app.providers.document.base import DocumentRetrievalProvider
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider


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
    document_provider: DocumentRetrievalProvider | None = None,
):
    """Build the DeepVerify research graph with injected providers."""

    search_provider = search or create_search_provider()

    document_retrieval_provider = (
        document_provider or create_document_retrieval_provider()
    )

    builder = StateGraph(DeepVerifyGraphState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    builder.add_node(
        "planner",
        make_planner_node(llm),
    )

    builder.add_node(
        "web_researcher",
        make_web_researcher_node(search_provider),
    )

    builder.add_node(
        "document_researcher",
        make_document_researcher_node(
            document_retrieval_provider
        ),
    )

    builder.add_node(
        "claim_extractor",
        make_claim_extractor_node(llm),
    )

    builder.add_node(
        "fact_checker",
        make_fact_checker_node(llm),
    )

    builder.add_node(
        "revision_decider",
        revision_decider_node,
    )

    builder.add_node(
        "revision_researcher",
        make_revision_researcher_node(search_provider),
    )

    # NEW: final research dossier writer
    builder.add_node(
        "writer",
        make_writer_node(llm),
    )

    # ---------------------------------------------------------
    # Main workflow
    # ---------------------------------------------------------

    builder.add_edge(START, "planner")

    # Fan-out: both research nodes run in parallel after planning.
    builder.add_edge("planner", "web_researcher")
    builder.add_edge("planner", "document_researcher")

    # Fan-in: both research branches feed the claim extractor.
    builder.add_edge("web_researcher", "claim_extractor")
    builder.add_edge("document_researcher", "claim_extractor")

    builder.add_edge(
        "claim_extractor",
        "fact_checker",
    )

    builder.add_edge(
        "fact_checker",
        "revision_decider",
    )

    # ---------------------------------------------------------
    # Revision routing
    # ---------------------------------------------------------

    builder.add_conditional_edges(
        "revision_decider",
        route_revision,
        {
            "revise": "revision_researcher",

            # CHANGED:
            # Previously this went directly to END.
            # Now the verified claims go to the writer first.
            "finish": "writer",
        },
    )

    # Revision research goes back through fact checking.
    builder.add_edge(
        "revision_researcher",
        "fact_checker",
    )

    # NEW: writer is the final step before END.
    builder.add_edge(
        "writer",
        END,
    )

    return builder.compile()