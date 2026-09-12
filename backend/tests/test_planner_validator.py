"""Tests for planner output validation."""

from __future__ import annotations

import pytest

from app.agents.planner_validator import PlannerValidationError, validate_planner_output


def _valid_subtasks() -> list[dict]:
    return [
        {
            "id": "consensus",
            "title": "Consensus / established facts",
            "query": "What is the consensus on topic X?",
            "purpose": "consensus",
            "priority": 1,
            "status": "pending",
        },
        {
            "id": "empirical",
            "title": "Empirical data / benchmarks / quantitative evidence",
            "query": "What benchmarks exist for topic X?",
            "purpose": "empirical",
            "priority": 2,
            "status": "pending",
        },
        {
            "id": "counterarguments",
            "title": "Counterarguments / limitations / competing perspectives",
            "query": "What are limitations of topic X?",
            "purpose": "counterarguments",
            "priority": 3,
            "status": "pending",
        },
    ]


def test_validate_planner_output_accepts_valid_plan() -> None:
    plan = validate_planner_output(
        {"topic": "AI safety", "subtasks": _valid_subtasks()},
        topic="AI safety",
    )
    assert plan.topic == "AI safety"
    assert len(plan.subtasks) == 3
    assert {s.purpose for s in plan.subtasks} == {
        "consensus",
        "empirical",
        "counterarguments",
    }


def test_validate_planner_output_rejects_wrong_count() -> None:
    subtasks = _valid_subtasks()[:2]
    with pytest.raises(PlannerValidationError, match="exactly 3 subtasks"):
        validate_planner_output({"subtasks": subtasks}, topic="test")


def test_validate_planner_output_rejects_missing_purpose() -> None:
    subtasks = _valid_subtasks()
    subtasks[2]["purpose"] = "consensus"
    with pytest.raises(PlannerValidationError, match="cover all required categories"):
        validate_planner_output({"subtasks": subtasks}, topic="test")


def test_validate_planner_output_rejects_blank_query() -> None:
    subtasks = _valid_subtasks()
    subtasks[0]["query"] = "   "
    with pytest.raises(PlannerValidationError, match="query must be a non-empty string"):
        validate_planner_output({"subtasks": subtasks}, topic="test")


def test_validate_planner_output_rejects_invalid_status() -> None:
    subtasks = _valid_subtasks()
    subtasks[1]["status"] = "unknown"
    with pytest.raises(PlannerValidationError, match="status must be one of"):
        validate_planner_output({"subtasks": subtasks}, topic="test")


def test_validate_planner_output_rejects_duplicate_ids() -> None:
    subtasks = _valid_subtasks()
    subtasks[2]["id"] = "consensus"
    with pytest.raises(PlannerValidationError, match="ids must be unique"):
        validate_planner_output({"subtasks": subtasks}, topic="test")


def test_validate_planner_output_rejects_non_object() -> None:
    with pytest.raises(PlannerValidationError, match="must be a JSON object"):
        validate_planner_output(["not", "a", "dict"], topic="test")
