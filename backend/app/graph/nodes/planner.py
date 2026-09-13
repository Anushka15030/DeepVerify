"""Planner graph node."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.planner import Planner
from app.agents.planner_validator import PlannerValidationError
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


def make_planner_node(llm: LLMProvider):

    """Create a planner node bound to the given LLM provider."""

    async def planner_node(state: DeepVerifyGraphState) -> dict[str, Any]:
        run_id = state.run_id
        question = state.original_question
        planner = Planner(llm)

        try:
            plan = await planner.plan(question)
        except PlannerValidationError as exc:
            error_event = AgentEvent(
                type="error",
                run_id=run_id,
                payload={"agent": "planner", "message": str(exc)},
                timestamp=datetime.now(timezone.utc),
            )
            return {
                "errors": [str(exc)],
                "agent_events": [error_event],
            }

        plan_event = AgentEvent(
            type="plan_created",
            run_id=run_id,
            payload={
                "agent": "planner",
                "topic": plan.topic,
                "subtask_count": len(plan.subtasks),
                "subtasks": [
                    subtask.model_dump(mode="json")
                    for subtask in plan.subtasks
                ],
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "research_plan": plan,
            "agent_events": [plan_event],
        }

    return planner_node

