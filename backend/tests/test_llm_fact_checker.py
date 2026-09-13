from datetime import datetime, timezone

import pytest

from app.agents.llm_fact_checker import LLMFactChecker
from app.core.models import Evidence, SourceMetadata


class FakeLLM:
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return """
        {
          "verdict": "supported",
          "grounding_score": 0.95,
          "explanation": "The evidence directly supports the claim.",
          "evidence_indices": [0]
        }
        """


class InvalidJSONLLM:
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return "not valid json"


def make_evidence(text: str) -> Evidence:
    source = SourceMetadata(
        url="https://example.com",
        title="Example Source",
        snippet=text,
        provider="test",
        retrieved_at=datetime.now(timezone.utc),
    )

    return Evidence(
        excerpt=text,
        sources=[source],
        confidence=0.9,
    )


@pytest.mark.asyncio
async def test_llm_fact_checker_returns_supported_claim() -> None:
    checker = LLMFactChecker(FakeLLM())

    evidence = [
        make_evidence(
            "India added 12 GW of solar capacity in 2025."
        )
    ]

    result = await checker.check_claim(
        "India added 12 GW of solar capacity in 2025.",
        evidence,
    )

    assert result.claim == (
        "India added 12 GW of solar capacity in 2025."
    )
    assert result.verdict == "supported"
    assert result.grounding_score == 0.95
    assert len(result.evidence) == 1
    assert result.explanation


@pytest.mark.asyncio
async def test_llm_fact_checker_handles_no_evidence() -> None:
    checker = LLMFactChecker(FakeLLM())

    result = await checker.check_claim(
        "India added 12 GW of solar capacity.",
        [],
    )

    assert result.verdict == "unverifiable"
    assert result.grounding_score == 0.0
    assert result.evidence == []


@pytest.mark.asyncio
async def test_llm_fact_checker_rejects_invalid_json() -> None:
    checker = LLMFactChecker(InvalidJSONLLM())

    evidence = [
        make_evidence("Some factual evidence.")
    ]

    with pytest.raises(ValueError, match="invalid JSON"):
        await checker.check_claim(
            "Some factual claim.",
            evidence,
        )