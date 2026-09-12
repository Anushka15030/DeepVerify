"""Tests for the Planner agent."""

from __future__ import annotations

import json

import pytest

from app.agents.planner import Planner
from app.agents.planner_validator import PlannerValidationError
from app.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_planner_produces_exactly_three_subtasks() -> None:
    planner = Planner(MockLLMProvider())
    plan = await planner.plan("What are the effects of climate change on agriculture?")
    assert len(plan.subtasks) == 3


@pytest.mark.asyncio
async def test_planner_subtasks_have_required_fields() -> None:
    planner = Planner(MockLLMProvider())
    plan = await planner.plan("Quantum computing applications")
    for subtask in plan.subtasks:
        assert subtask.id
        assert subtask.title
        assert subtask.query
        assert subtask.purpose in {"consensus", "empirical", "counterarguments"}
        assert 1 <= subtask.priority <= 10
        assert subtask.status == "pending"


@pytest.mark.asyncio
async def test_planner_covers_all_categories() -> None:
    planner = Planner(MockLLMProvider())
    plan = await planner.plan("Renewable energy trends")
    purposes = {subtask.purpose for subtask in plan.subtasks}
    assert purposes == {"consensus", "empirical", "counterarguments"}


@pytest.mark.asyncio
async def test_planner_is_deterministic_in_mock_mode() -> None:
    provider = MockLLMProvider(model="mock-gpt")
    planner = Planner(provider)
    question = "Neural network interpretability"
    first = await planner.plan(question)
    second = await planner.plan(question)
    assert first.model_dump() == second.model_dump()


class _BadJSONLLM:
    async def complete(self, prompt: str, system: str | None = None) -> str:
        return "not json at all"


class _InvalidPlanLLM:
    async def complete(self, prompt: str, system: str | None = None) -> str:
        return json.dumps({"subtasks": [{"id": "only-one", "query": "x"}]})


@pytest.mark.asyncio
async def test_planner_rejects_invalid_json() -> None:
    planner = Planner(_BadJSONLLM())
    with pytest.raises(PlannerValidationError, match="does not contain valid JSON"):
        await planner.plan("test question")


@pytest.mark.asyncio
async def test_planner_rejects_malformed_plan() -> None:
    planner = Planner(_InvalidPlanLLM())
    with pytest.raises(PlannerValidationError, match="exactly 3 subtasks"):
        await planner.plan("test question")
