"""Service for running the DeepVerify LangGraph research workflow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.config import (
    create_llm_provider,
    create_search_provider,
    get_settings,
)
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyState, initial_graph_state
from app.graph.workflow import build_research_graph
from app.providers.llm.base import LLMProvider
from app.providers.search.base import SearchProvider


async def run_research(
    question: str,
    *,
    run_id: str | None = None,
    llm: LLMProvider | None = None,
    search: SearchProvider | None = None,
) -> DeepVerifyState:
    """Execute the research graph and return the final state."""

    resolved_run_id = run_id or str(uuid.uuid4())

    settings = get_settings()

    llm_provider = llm or create_llm_provider(settings)
    search_provider = search or create_search_provider(settings)

    graph = build_research_graph(
        llm=llm_provider,
        search=search_provider,
    )

    initial = initial_graph_state(
        question,
        resolved_run_id,
    )

    final = await graph.ainvoke(initial)

    state = DeepVerifyState.model_validate(final)

    completion_event = AgentEvent(
        type="run_completed",
        run_id=resolved_run_id,
        payload={
            "question": question,
            "subtask_count": (
                len(state.research_plan.subtasks)
                if state.research_plan
                else 0
            ),
            "error_count": len(state.errors),
        },
        timestamp=datetime.now(timezone.utc),
    )

    state.agent_events.append(completion_event)

    return state