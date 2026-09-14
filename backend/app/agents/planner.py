"""Planner agent: decomposes a research question into three subtasks."""



from __future__ import annotations



import json

import re



from app.agents.planner_validator import PlannerValidationError, validate_planner_output

from app.core.models import ResearchPlan

from app.providers.llm.base import LLMProvider

from app.providers.llm.mock import PLANNER_SYSTEM_MARKER



PLANNER_SYSTEM_PROMPT = (
    f"{PLANNER_SYSTEM_MARKER}\n"
    "You are a research planner for an autonomous fact-checking system.\n\n"
    "Decompose the user's question into EXACTLY THREE subtasks.\n"
    "The three subtasks MUST have these exact purpose values, one each:\n"
    '1. "consensus" — established facts, commonly accepted findings, or expert consensus.\n'
    '2. "empirical" — quantitative evidence, measurements, benchmarks, experiments, or data.\n'
    '3. "counterarguments" — limitations, opposing evidence, criticisms, or alternative explanations.\n\n'
    "IMPORTANT:\n"
    "- The purpose field MUST be exactly one of: "
    '"consensus", "empirical", "counterarguments".\n'
    "- Do not use synonyms such as "
    '"general", "facts", "quantitative", "limitations", "criticism", '
    '"background", or "research".\n'
    "- Include exactly one subtask for each purpose.\n"
    "- Return JSON only. Do not use Markdown fences or explanatory text.\n\n"
    "Required JSON structure:\n"
    '{"topic": "<question>", "subtasks": ['
    '{"id": "consensus", "title": "...", "query": "...", '
    '"purpose": "consensus", "priority": 1, "status": "pending"}, '
    '{"id": "empirical", "title": "...", "query": "...", '
    '"purpose": "empirical", "priority": 1, "status": "pending"}, '
    '{"id": "counterarguments", "title": "...", "query": "...", '
    '"purpose": "counterarguments", "priority": 1, "status": "pending"}'
    "]}"
)



_JSON_BLOCK_PATTERN = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)





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

        raw_response = await self._llm.complete(question, system=PLANNER_SYSTEM_PROMPT)

        try:

            parsed = self._extract_json(raw_response)

        except json.JSONDecodeError as exc:

            raise PlannerValidationError(f"planner response is not valid JSON: {exc}") from exc



        return validate_planner_output(parsed, topic=question)


