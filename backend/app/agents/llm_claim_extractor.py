"""LLM-powered claim extraction for DeepVerify."""

from __future__ import annotations

import json

from app.core.models import ExtractedClaim
from app.providers.llm.base import LLMProvider


class LLMClaimExtractor:
    """Extract structured factual claims using an LLM."""

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def extract(
        self,
        text: str,
    ) -> list[ExtractedClaim]:
        """Extract structured claims from research text."""

        if not text.strip():
            return []

        system = """
You are a research claim extraction agent.

Extract only factual claims from the provided research text.

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
Do not include questions.
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
            raise ValueError(
                "LLM claim extractor returned invalid JSON."
            ) from exc

        if not isinstance(data, list):
            raise ValueError(
                "LLM claim extractor must return a JSON array."
            )

        claims: list[ExtractedClaim] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            claims.append(
                ExtractedClaim.model_validate(item)
            )

        return claims