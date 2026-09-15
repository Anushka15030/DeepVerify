"""LLM-based fact-checking agent for DeepVerify."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.models import ClaimCheck, Evidence


class LLMFactChecker:
    """Fact-check claims using an LLM and supplied evidence."""

    def __init__(self, llm: Any) -> None:
        self.llm = llm

    async def check_claim(
        self,
        claim: str,
        evidence: list[Evidence],
    ) -> ClaimCheck:
        """Verify a claim against supplied evidence."""

        if not claim.strip():
            raise ValueError("claim must not be blank")

        usable_evidence = [
            item
            for item in evidence
            if item.excerpt.strip()
        ]

        if not usable_evidence:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                verification_method="llm",
                explanation=(
                    "No evidence was available to verify this claim."
                ),
            )

        evidence_text = "\n\n".join(
            f"[{index}] {item.excerpt.strip()}"
            for index, item in enumerate(usable_evidence)
        )

        prompt = f"""
You are a careful fact-checking system.

Verify the following claim using ONLY the supplied evidence.

Claim:
{claim}

Evidence:
{evidence_text}

Verdict must be exactly one of:
supported, refuted, unverifiable, inconclusive

Use:
- supported = evidence directly supports the claim
- refuted = evidence directly conflicts with the claim
- unverifiable = evidence is insufficient to verify the claim
- inconclusive = evidence is relevant but ambiguous or conflicting

Return ONLY valid JSON in this exact structure:

{{
  "verdict": "supported",
  "grounding_score": 0.0,
  "explanation": "Brief explanation based on the evidence.",
  "evidence_indices": [0]
}}

Rules:
- grounding_score must be between 0.0 and 1.0.
- evidence_indices must contain only indices from the supplied evidence.
- Select only evidence that directly supports or contradicts the claim.
- Do not invent evidence.
- Do not use information outside the supplied evidence.
- Keep the explanation concise and evidence-based.
""".strip()

        system = (
            "You are a precise fact-checking assistant. "
            "Return only valid JSON and never invent evidence."
        )

        response = await self.llm.complete(
            prompt,
            system=system,
        )

        data = self._parse_response(response)

        allowed_verdicts = {
            "supported",
            "refuted",
            "unverifiable",
            "inconclusive",
        }

        verdict = data.get("verdict")

        if verdict not in allowed_verdicts:
            raise ValueError(
                f"invalid verdict: {verdict}"
            )

        grounding_score = data.get("grounding_score")

        if not isinstance(grounding_score, (int, float)):
            raise ValueError(
                "grounding_score must be a number"
            )

        grounding_score = float(grounding_score)

        if not 0.0 <= grounding_score <= 1.0:
            raise ValueError(
                "grounding_score must be between 0.0 and 1.0"
            )

        explanation = data.get("explanation", "")

        if not isinstance(explanation, str):
            explanation = str(explanation)

        evidence_indices = data.get("evidence_indices", [])

        if not isinstance(evidence_indices, list):
            raise ValueError(
                "evidence_indices must be a list"
            )

        selected_evidence: list[Evidence] = []

        for index in evidence_indices:
            if not isinstance(index, int):
                continue

            if 0 <= index < len(usable_evidence):
                selected_evidence.append(
                    usable_evidence[index]
                )

        return ClaimCheck(
            claim=claim,
            verdict=verdict,
            evidence=selected_evidence,
            grounding_score=grounding_score,
            verification_method="llm",
            explanation=explanation,
        )

    @staticmethod
    def _parse_response(response: str) -> dict[str, Any]:
        """Parse JSON returned by the LLM."""

        cleaned = response.strip()

        # Remove Markdown code fences if the model returns them.
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        )

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "invalid JSON returned by LLM"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "LLM response must be a JSON object"
            )

        return data