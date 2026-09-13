"""Planner agent: decomposes a research question into three subtasks."""

from __future__ import annotations

import json
import re

from app.agents.planner_validator import (
    PlannerValidationError,
    validate_planner_output,
)
from app.core.models import ResearchPlan
from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import PLANNER_SYSTEM_MARKER

PLANNER_SYSTEM_PROMPT = (
    f"{PLANNER_SYSTEM_MARKER}\n"
    "You are a research planner. Decompose the user's question into exactly three "
    "subtasks covering: consensus/established facts, empirical/quantitative evidence, "
    "and counterarguments/limitations. Respond with JSON only:\n"
    '{"topic": "<question>", "subtasks": ['
    '{"id": "consensus", "title": "...", "query": "...", "purpose": "consensus", '
    '"priority": 1, "status": "pending"}, ...]}'
)

_JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class Planner:
    """Produces a validated three-subtask research plan from a question."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    @staticmethod
    def _extract_json(raw: str) -> object:
        stripped = raw.strip()
        if stripped.startswith("{"):
            return json.loads(stripped)

        match = _JSON_BLOCK_PATTERN.search(raw)
        if match:
            return json.loads(match.group(1))

        raise PlannerValidationError("planner response does not contain valid JSON")

    async def plan(self, question: str) -> ResearchPlan:
        """Generate and validate a research plan for the given question."""
        raw_response = await self._llm.complete(
            question,
            system=PLANNER_SYSTEM_PROMPT,
        )
        try:
            parsed = self._extract_json(raw_response)
        except json.JSONDecodeError as exc:
            raise PlannerValidationError(
                f"planner response is not valid JSON: {exc}"
            ) from exc

        return validate_planner_output(parsed, topic=question)