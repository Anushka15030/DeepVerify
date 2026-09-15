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

    async def extract(
        self,
        text: str,
        research_question: str | None = None,
    ) -> list[ExtractedClaim]:
        """Extract atomic, independently verifiable claims."""

        if not text.strip():
            return []

        question_context = (
            research_question.strip()
            if research_question and research_question.strip()
            else "No specific research question was provided."
        )

        system = """
You are a research claim extraction agent for an autonomous
fact-checking system.

Your task is to extract the most important factual claims from
the supplied research evidence that directly answer the research
question.

A VALID CLAIM MUST:
- be an objective factual assertion about the research topic
- be independently verifiable using evidence
- contain one main proposition
- be directly relevant to the research question
- be supported by the supplied research text
- stand on its own without referring to "the paper", "the study",
  "the authors", "the research", or "the evidence"

Prefer:
- quantitative or statistical claims
- concrete factual claims
- important comparisons
- supported causal claims
- important temporal claims
- specific limitations or findings relevant to the question

DO NOT extract:
- statements about what a paper, study, or author discusses
- article or paper metadata
- headings or section descriptions
- recommendations presented as established facts
- vague claims such as "AI has many challenges"
- opinions or speculation
- questions
- minor background details
- duplicate or near-duplicate claims
- compound claims containing several independently verifiable
  propositions

If a sentence contains multiple distinct factual propositions,
split them into separate claims when appropriate.

Prefer a specific, independently verifiable statement such as:
"AI fact-checking systems can struggle to interpret sarcasm and satire."

Do NOT produce a meta-level statement such as:
"The research discusses difficulties in interpreting sarcasm and satire."

Extract fewer claims rather than producing low-value claims.

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
""".strip()

        prompt = f"""
Research question:
{question_context}

Research evidence:
{text}

Extract only the high-value factual claims that directly help answer
the research question.
""".strip()

        response = await self.llm.complete(
            prompt=prompt,
            system=system,
        )

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON for claim extraction."
            ) from exc

        if not isinstance(data, list):
            raise ValueError(
                "LLM claim extraction response must be a JSON array."
            )

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