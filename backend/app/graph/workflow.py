"""LangGraph workflow definition for DeepVerify Phase 2."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.document_researcher import document_researcher_node
from app.graph.nodes.planner import make_planner_node
from app.graph.nodes.web_researcher import web_researcher_node
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


def build_research_graph(llm: LLMProvider):
    """Build the Phase 2 research graph: planner → parallel research placeholders."""
    builder = StateGraph(DeepVerifyGraphState)

    builder.add_node("planner", make_planner_node(llm))
    builder.add_node("web_researcher", web_researcher_node)
    builder.add_node("document_researcher", document_researcher_node)

    builder.add_edge(START, "planner")
    # Fan-out: both research nodes run in parallel after planning (Phase 3 swap point).
    builder.add_edge("planner", "web_researcher")
    builder.add_edge("planner", "document_researcher")
    # Fan-in: graph completes once both branches finish.
    builder.add_edge("web_researcher", END)
    builder.add_edge("document_researcher", END)

    return builder.compile()
