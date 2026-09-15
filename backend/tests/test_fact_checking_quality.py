import pytest

from app.agents.llm_fact_checker import LLMFactChecker
from app.core.models import Evidence, SourceMetadata


class FakeLLM:
    def __init__(self, response: str):
        self.response = response

    async def complete(self, prompt: str, system: str) -> str:
        return self.response


def make_evidence(text: str, confidence: float = 0.9) -> Evidence:
    return Evidence(
        excerpt=text,
        confidence=confidence,
        sources=[
            SourceMetadata(
                url="https://example.com",
                title="Example source",
                snippet=text,
                retrieved_at="2026-01-01T00:00:00Z",
                provider="test",
            )
        ],
    )


@pytest.mark.asyncio
async def test_llm_fact_checker_supported_claim():
    llm = FakeLLM(
        '{"verdict":"supported",'
        '"grounding_score":0.9,'
        '"explanation":"The evidence directly supports the claim.",'
        '"evidence_indices":[0]}'
    )

    checker = LLMFactChecker(llm)

    result = await checker.check_claim(
        "Python was created by Guido van Rossum.",
        [
            make_evidence(
                "Python was created by Guido van Rossum."
            )
        ],
    )

    assert result.verdict == "supported"
    assert result.verification_method == "llm"
    assert result.grounding_score == 0.9
    assert len(result.evidence) == 1


@pytest.mark.asyncio
async def test_llm_fact_checker_refuted_claim():
    llm = FakeLLM(
        '{"verdict":"refuted",'
        '"grounding_score":0.85,'
        '"explanation":"The evidence directly conflicts with the claim.",'
        '"evidence_indices":[0]}'
    )

    checker = LLMFactChecker(llm)

    result = await checker.check_claim(
        "Python was created in 2005.",
        [
            make_evidence(
                "Python was created by Guido van Rossum and first released in 1991."
            )
        ],
    )

    assert result.verdict == "refuted"
    assert result.verification_method == "llm"
    assert result.grounding_score == 0.85
    assert len(result.evidence) == 1


@pytest.mark.asyncio
async def test_llm_fact_checker_inconclusive_claim():
    llm = FakeLLM(
        '{"verdict":"inconclusive",'
        '"grounding_score":0.4,'
        '"explanation":"The evidence is relevant but does not resolve the claim.",'
        '"evidence_indices":[0]}'
    )

    checker = LLMFactChecker(llm)

    result = await checker.check_claim(
        "The algorithm is always the fastest.",
        [
            make_evidence(
                "The algorithm performs well on the reported benchmark."
            )
        ],
    )

    assert result.verdict == "inconclusive"
    assert result.verification_method == "llm"
    assert result.grounding_score == 0.4
    assert len(result.evidence) == 1