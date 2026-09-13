"""LLM-powered claim extraction for DeepVerify."""

from __future__ import annotations

import json

from app.core.models import ExtractedClaim
from app.providers.llm.base import LLMProvider


class LLMClaimExtractor:
    """Extract a small set of high-value factual claims using an LLM."""

    MAX_CLAIMS = 10

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def extract(self, text: str) -> list[ExtractedClaim]:
        if not text.strip():
            return []

        system = """
You are a research claim extraction agent.

Extract only the most important factual claims from the provided research text.

Prioritize:
- quantitative or statistical claims
- concrete factual claims
- important comparisons
- supported causal claims
- important temporal claims

Ignore:
- opinions
- recommendations
- questions
- vague statements
- repeated claims
- minor background details

Extract AT MOST 10 claims.

For each claim, classify it as exactly one of:
- quantitative
- factual
- comparative
- causal
- temporal
- general

Also assign importance:
- high
- medium
- low

Return ONLY a valid JSON array.

Each item must have exactly:
{
  "claim": "...",
  "claim_type": "...",
  "importance": "..."
}

Do not explain your answer.
Do not invent information.
"""

        prompt = f"""
Extract the important factual claims from this research text:

{text}
"""

        response = await self.llm.complete(
            prompt=prompt,
            system=system,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM returned invalid JSON for claim extraction.") from exc

        if not isinstance(data, list):
            raise ValueError("LLM claim extraction response must be a JSON array.")

        claims: list[ExtractedClaim] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                claim = ExtractedClaim.model_validate(item)
            except Exception:
                continue

            claims.append(claim)

            if len(claims) >= self.MAX_CLAIMS:
                break

        return claims