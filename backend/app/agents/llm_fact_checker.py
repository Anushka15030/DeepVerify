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
        """Verify one claim using only the supplied evidence."""

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

        evidence_text = "\n".join(
            f"[{index}] {item.excerpt.strip()}"
            for index, item in enumerate(evidence)
            if item.excerpt.strip()
        )

        if not evidence_text:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                verification_method="llm",
                explanation="Available evidence contained no usable excerpts.",
            )

        system = """
You are a strict fact-checking agent.

Verify ONE claim using ONLY the supplied evidence.

Verdict must be exactly one of:
supported, contradicted, unverifiable, inconclusive

Use:
- supported = evidence directly supports the claim
- contradicted = evidence directly conflicts with the claim
- unverifiable = evidence is insufficient
- inconclusive = evidence is relevant but ambiguous or conflicting

Return ONLY this JSON object:
{
  "verdict": "supported",
  "grounding_score": 0.0,
  "explanation": "brief evidence-based explanation",
  "evidence_indices": [0]
}

grounding_score must be between 0.0 and 1.0.

evidence_indices must contain only the zero-based evidence indices
that materially support the verdict.

Do not use outside knowledge.
Do not invent information.
Do not include markdown.
Do not include text outside the JSON object.
Keep the explanation under 40 words.
"""

        prompt = f"""Claim:
{claim.strip()}

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

        allowed_verdicts = {
            "supported",
            "contradicted",
            "unverifiable",
            "inconclusive",
        }

        if verdict not in allowed_verdicts:
            raise ValueError(
                f"Invalid fact-check verdict: {verdict!r}"
            )

        if not isinstance(grounding_score, (int, float)):
            raise ValueError(
                "grounding_score must be numeric."
            )

        grounding_score = max(
            0.0,
            min(1.0, float(grounding_score)),
        )

        if not isinstance(explanation, str):
            explanation = str(explanation)

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
            verification_method="llm",
            explanation=explanation,
        )
