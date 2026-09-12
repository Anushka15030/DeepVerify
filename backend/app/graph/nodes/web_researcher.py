"""Placeholder web research graph node (Phase 2 mock)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState


async def web_researcher_node(
    state: DeepVerifyGraphState,
) -> dict[str, Any]:
    """Emit a placeholder event; real web search is Phase 3."""

    run_id = state.run_id
    plan = state.research_plan

    subtask_ids = (
        [subtask.id for subtask in plan.subtasks]
        if plan
        else []
    )

    started = AgentEvent(
        type="search_started",
        run_id=run_id,
        payload={
            "agent": "web_researcher",
            "mode": "placeholder",
            "message": (
                "Web research placeholder — "
                "real search deferred to Phase 3"
            ),
            "subtask_ids": subtask_ids,
        },
        timestamp=datetime.now(timezone.utc),
    )

    completed = AgentEvent(
        type="search_completed",
        run_id=run_id,
        payload={
            "agent": "web_researcher",
            "mode": "placeholder",
            "results_count": 0,
        },
        timestamp=datetime.now(timezone.utc),
    )

    return {
        "agent_events": [started, completed],
    }