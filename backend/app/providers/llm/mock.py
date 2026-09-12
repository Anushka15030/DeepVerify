"""Deterministic mock LLM provider (no API key required)."""

from __future__ import annotations

import hashlib
import json

PLANNER_SYSTEM_MARKER = "deepverify-planner"

_PLANNER_CATEGORIES = (
    {
        "id": "consensus",
        "title": "Consensus / established facts",
        "purpose": "consensus",
        "priority": 1,
    },
    {
        "id": "empirical",
        "title": "Empirical data / benchmarks / quantitative evidence",
        "purpose": "empirical",
        "priority": 2,
    },
    {
        "id": "counterarguments",
        "title": "Counterarguments / limitations / competing perspectives",
        "purpose": "counterarguments",
        "priority": 3,
    },
)


class MockLLMProvider:
    """Returns deterministic completions based on prompt content hash."""

    def __init__(self, model: str = "mock-gpt") -> None:
        self.model = model

    @staticmethod
    def _prompt_digest(prompt: str, system: str | None = None) -> str:
        content = f"{system or ''}:{prompt}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _planner_response(self, question: str) -> str:
        """Return deterministic structured planner JSON for a research question."""
        digest = self._prompt_digest(question, PLANNER_SYSTEM_MARKER)
        subtasks = []
        for category in _PLANNER_CATEGORIES:
            subtasks.append(
                {
                    "id": category["id"],
                    "title": category["title"],
                    "query": f"{question} — focus: {category['purpose']} [{digest[:8]}]",
                    "purpose": category["purpose"],
                    "priority": category["priority"],
                    "status": "pending",
                }
            )
        return json.dumps({"topic": question, "subtasks": subtasks})

    async def complete(self, prompt: str, system: str | None = None) -> str:
        if system and PLANNER_SYSTEM_MARKER in system:
            return self._planner_response(prompt)

        digest = self._prompt_digest(prompt, system)
        system_note = f" system={system!r}" if system else ""
        return (
            f"[mock-llm model={self.model} hash={digest}]"
            f" Response for prompt ({len(prompt)} chars){system_note}."
        )
