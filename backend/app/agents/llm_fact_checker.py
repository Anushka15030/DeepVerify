"""LLM-powered fact checking for DeepVerify."""

from __future__ import annotations

import json

from app.core.models import ClaimCheck, Evidence
from app.providers.llm.base import LLMProvider


class LLMFactChecker:
    """Verify a claim against supplied evidence using an LLM."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def check_claim(
        self,
        claim: str,
        evidence: list[Evidence],
    ) -> ClaimCheck:
        if not claim.strip():
            raise ValueError("claim must not be blank")

        if not evidence:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                explanation="No evidence was available to verify this claim.",
            )

        evidence_text = "\n\n".join(
            f"[Evidence {index}]\n{item.excerpt}"
            for index, item in enumerate(evidence)
        )

        system = """
You are the fact-checking agent in a research verification system.

Your task is to verify ONE claim using ONLY the supplied evidence.

Classify the claim as exactly one of:
- supported
- contradicted
- unverifiable
- inconclusive

Definitions:
- supported: the evidence directly supports the claim.
- contradicted: the evidence directly conflicts with the claim.
- unverifiable: the evidence does not contain enough information to determine whether the claim is true.
- inconclusive: the evidence is relevant but ambiguous, incomplete, or conflicting.

Assign a grounding_score from 0.0 to 1.0:
- 0.0 = completely unsupported
- 0.5 = partially grounded or inconclusive
- 1.0 = strongly grounded

Return ONLY valid JSON.

The JSON must contain exactly:
{
  "verdict": "...",
  "grounding_score": 0.0,
  "explanation": "...",
  "evidence_indices": [0]
}

evidence_indices must contain the zero-based indices of evidence items
that materially support your decision.

Do not invent evidence.
Do not use outside knowledge.
Do not include markdown.
Do not include any text outside the JSON object.
"""

        prompt = f"""
Claim:
{claim}

Evidence:
{evidence_text}
"""

        response = await self.llm.complete(
            prompt=prompt,
            system=system,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM fact checker returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "LLM fact checker must return a JSON object."
            )

        verdict = data.get("verdict")
        grounding_score = data.get("grounding_score")
        explanation = data.get("explanation", "")
        evidence_indices = data.get("evidence_indices", [])

        if not isinstance(evidence_indices, list):
            raise ValueError(
                "evidence_indices must be a JSON array."
            )

        selected_evidence: list[Evidence] = []

        for index in evidence_indices:
            if isinstance(index, int) and 0 <= index < len(evidence):
                selected_evidence.append(evidence[index])

        return ClaimCheck(
            claim=claim,
            verdict=verdict,
            evidence=selected_evidence,
            grounding_score=grounding_score,
            explanation=explanation,
        )