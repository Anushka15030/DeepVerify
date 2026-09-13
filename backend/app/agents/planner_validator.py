"""Validation for structured planner output."""

from __future__ import annotations

from app.core.models import ResearchPlan, ResearchSubtask, SubtaskPurpose

REQUIRED_PURPOSES: frozenset[SubtaskPurpose] = frozenset(
    {"consensus", "empirical", "counterarguments"}
)

PURPOSE_TITLES: dict[SubtaskPurpose, str] = {
    "consensus": "Consensus / established facts",
    "empirical": "Empirical data / benchmarks / quantitative evidence",
    "counterarguments": "Counterarguments / limitations / competing perspectives",
}

VALID_STATUSES = frozenset({"pending", "in_progress", "completed", "failed", "skipped"})


class PlannerValidationError(ValueError):
    """Raised when planner output fails structural validation."""


def _validate_subtask_raw(raw: object, index: int) -> ResearchSubtask:
    if not isinstance(raw, dict):
        raise PlannerValidationError(f"subtasks[{index}] must be an object")

    required_fields = ("id", "title", "query", "purpose", "priority", "status")
    for field in required_fields:
        if field not in raw:
            raise PlannerValidationError(f"subtasks[{index}] missing required field: {field}")

    subtask_id = raw["id"]
    title = raw["title"]
    query = raw["query"]
    purpose = raw["purpose"]
    priority = raw["priority"]
    status = raw["status"]

    if not isinstance(subtask_id, str) or not subtask_id.strip():
        raise PlannerValidationError(f"subtasks[{index}].id must be a non-empty string")
    if not isinstance(title, str) or not title.strip():
        raise PlannerValidationError(f"subtasks[{index}].title must be a non-empty string")
    if not isinstance(query, str) or not query.strip():
        raise PlannerValidationError(f"subtasks[{index}].query must be a non-empty string")
    if purpose not in REQUIRED_PURPOSES:
        raise PlannerValidationError(
            f"subtasks[{index}].purpose must be one of {sorted(REQUIRED_PURPOSES)}"
        )
    if not isinstance(priority, int) or not (1 <= priority <= 10):
        raise PlannerValidationError(f"subtasks[{index}].priority must be an integer 1-10")
    if status not in VALID_STATUSES:
        raise PlannerValidationError(
            f"subtasks[{index}].status must be one of {sorted(VALID_STATUSES)}"
        )

    return ResearchSubtask(
        id=subtask_id.strip(),
        title=title.strip(),
        query=query.strip(),
        purpose=purpose,
        priority=priority,
        status=status,
    )


def validate_planner_output(data: object, *, topic: str) -> ResearchPlan:
    """Validate and normalize raw planner output into a ResearchPlan."""
    if not isinstance(data, dict):
        raise PlannerValidationError("planner output must be a JSON object")

    raw_subtasks = data.get("subtasks")
    if not isinstance(raw_subtasks, list):
        raise PlannerValidationError("planner output must include a subtasks array")

    if len(raw_subtasks) != 3:
        raise PlannerValidationError(
            f"planner must produce exactly 3 subtasks, got {len(raw_subtasks)}"
        )

    subtasks = [_validate_subtask_raw(raw, i) for i, raw in enumerate(raw_subtasks)]

    purposes = {subtask.purpose for subtask in subtasks}
    if purposes != REQUIRED_PURPOSES:
        missing = REQUIRED_PURPOSES - purposes
        extra = purposes - REQUIRED_PURPOSES
        details: list[str] = []
        if missing:
            details.append(f"missing purposes: {sorted(missing)}")
        if extra:
            details.append(f"unexpected purposes: {sorted(extra)}")
        raise PlannerValidationError(
            "planner subtasks must cover all required categories: "
            + "; ".join(details)
        )

    ids = [subtask.id for subtask in subtasks]
    if len(set(ids)) != 3:
        raise PlannerValidationError("planner subtask ids must be unique")

    plan_topic = data.get("topic", topic)
    if not isinstance(plan_topic, str) or not plan_topic.strip():
        plan_topic = topic

    return ResearchPlan(topic=plan_topic.strip(), subtasks=subtasks)