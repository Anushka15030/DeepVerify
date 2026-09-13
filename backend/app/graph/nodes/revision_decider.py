"""LangGraph node for deciding whether research should be revised."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.revision_decider import RevisionDecider
from app.core.config import get_settings
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState


async def revision_decider_node(
    state: DeepVerifyGraphState,
) -> dict[str, Any]:
    """Decide whether another research iteration is required."""

    run_id = state.run_id
    settings = get_settings()

    decider = RevisionDecider(settings)

    grounding_score = state.grounding_score
    revision_count = state.revision_count

    should_revise = decider.should_revise(
        grounding_score=grounding_score,
        revision_count=revision_count,
    )

    queries = (
        decider.build_queries(state.claim_checks)
        if should_revise
        else []
    )

    event = AgentEvent(
        type="revision_requested" if should_revise else "revision_not_needed",
        run_id=run_id,
        payload={
            "agent": "revision_decider",
            "grounding_score": grounding_score,
            "threshold": settings.grounding_pass_threshold,
            "revision_count": revision_count,
            "max_iterations": settings.max_research_iterations,
            "should_revise": should_revise,
            "queries_count": len(queries),
        },
        timestamp=datetime.now(timezone.utc),
    )

    return {
    "revision_count": revision_count + 1 if should_revise else revision_count,
    "revision_queries": queries,
    "agent_events": [event],
    }