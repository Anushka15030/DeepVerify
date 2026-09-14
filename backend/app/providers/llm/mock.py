"""Deterministic mock LLM provider (no API key required)."""

from __future__ import annotations

import hashlib
import json

PLANNER_SYSTEM_MARKER = "deepverify-planner"
FACT_CHECKER_SYSTEM_MARKER = "strict fact-checking agent"

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
    """Returns deterministic completions based on prompt content."""

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
                    "query": (
                        f"{question} — focus: "
                        f"{category['purpose']} [{digest[:8]}]"
                    ),
                    "purpose": category["purpose"],
                    "priority": category["priority"],
                    "status": "pending",
                }
            )

        return json.dumps(
            {
                "topic": question,
                "subtasks": subtasks,
            }
        )

    def _fact_checker_response(self, prompt: str) -> str:
        """
        Return deterministic fact-checking JSON for fallback/demo runs.

        The graph has already selected a small set of relevant evidence
        for the claim. The mock preserves that evidence rather than
        pretending to perform semantic verification.
        """

        prompt_lower = prompt.lower()

        if "evidence:" not in prompt_lower:
            return json.dumps(
                {
                    "verdict": "unverifiable",
                    "grounding_score": 0.0,
                    "explanation": "No evidence was available to verify this claim.",
                    "evidence_indices": [],
                }
            )

        evidence_section = prompt.split("Evidence:", 1)[1]

        evidence_indices: list[int] = []

        for line in evidence_section.splitlines():
            line = line.strip()

            if line.startswith("["):
                closing = line.find("]")

                if closing > 1:
                    index_text = line[1:closing]

                    if index_text.isdigit():
                        evidence_indices.append(int(index_text))

        # The graph has already selected the most relevant evidence.
        # Preserve those selections in the fallback path.
        if not evidence_indices:
            return json.dumps(
                {
                    "verdict": "unverifiable",
                    "grounding_score": 0.0,
                    "explanation": "No usable evidence indices were available.",
                    "evidence_indices": [],
                }
            )

        return json.dumps(
            {
                "verdict": "inconclusive",
                "grounding_score": 0.75,
                "explanation": (
                    "Relevant supplied evidence is available, "
                    "but semantic verification is unavailable in fallback mode."
                ),
                "evidence_indices": evidence_indices,
            }
        )

    def _writer_response(self, prompt: str) -> str:
        """Return a deterministic citation-aware research dossier."""

        import re

        citation_numbers = re.findall(
            r"EVIDENCE \[(\d+)\]:",
            prompt,
        )

        # Keep only unique citation numbers while preserving order.
        citations: list[str] = []

        for number in citation_numbers:
            if number not in citations:
                citations.append(number)

        def citation(index: int) -> str:
            if index < len(citations):
                return f" [{citations[index]}]"
            return ""

        return f"""# Research Dossier

## Executive Summary

AI-powered fact-checking systems face several major challenges, including contextual ambiguity, nuanced misinformation, sarcasm and satire, training-data bias, and continuously evolving misinformation. Human oversight remains important for difficult or ambiguous cases.{citation(0)}

## Key Findings

- **Context and nuance:** AI fact-checking systems can struggle with sarcasm, satire, parody, and claims containing both accurate and misleading information.{citation(0)}
- **Training-data bias:** Limitations or biases in training data can affect the reliability of AI fact-checking decisions.{citation(1)}
- **Evolving misinformation:** Misinformation techniques continuously change, creating difficulties for systems trained on earlier patterns.{citation(2)}
- **Human oversight:** Difficult and ambiguous cases may still require additional human intervention.{citation(0)}
- **Verification complexity:** Automated fact-checking requires contextual interpretation rather than simple information matching.{citation(1)}

## Evidence and Analysis

The supplied evidence identifies contextual understanding as a central limitation. Sarcasm, satire, parody, and partially accurate claims can make automated classification difficult.{citation(0)}

Training data is another important concern because limitations or biases in the data can influence AI fact-checking results.{citation(1)}

The evidence also indicates that misinformation techniques evolve over time. This creates a moving-target problem in which systems must adapt to new forms of misinformation.{citation(2)}

Proposed directions include improved training data, stronger deepfake detection, cross-platform collaboration, blockchain-based verification, and hybrid AI-human intervention.{citation(0)}

## Limitations and Counterarguments

The supplied evidence identifies important challenges but does not provide quantitative benchmark results establishing the relative severity or frequency of each challenge. Therefore, these findings should be treated as identified limitations rather than quantified conclusions.{citation(0)}

## Conclusion

The major challenges for AI fact-checking are contextual ambiguity, training-data bias, evolving misinformation, and the continuing need for human judgment. The evidence supports a hybrid approach in which AI assists fact-checking while difficult or ambiguous cases receive additional human oversight.{citation(0)}
"""

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:

        if system and PLANNER_SYSTEM_MARKER in system:
            return self._planner_response(prompt)

        if system and FACT_CHECKER_SYSTEM_MARKER in system.lower():
            return self._fact_checker_response(prompt)

        if system and "final research dossier writer" in system.lower():
            return self._writer_response(prompt)

        digest = self._prompt_digest(prompt, system)
        system_note = f" system={system!r}" if system else ""

        return (
            f"[mock-llm model={self.model} hash={digest}]"
            f" Response for prompt ({len(prompt)} chars){system_note}."
        )