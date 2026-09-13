import pytest

from app.agents.llm_claim_extractor import LLMClaimExtractor
from app.providers.llm.base import LLMProvider


class FakeLLM:
    """Deterministic fake LLM for unit tests."""

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return """
        [
            {
                "claim": "The benchmark achieved an accuracy of 95 percent.",
                "claim_type": "quantitative",
                "importance": "high"
            },
            {
                "claim": "The proposed method outperformed the baseline.",
                "claim_type": "comparative",
                "importance": "medium"
            }
        ]
        """


class InvalidJSONLLM:
    """Fake LLM that returns invalid JSON."""

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return "This is not JSON"


@pytest.mark.asyncio
async def test_llm_claim_extractor_returns_structured_claims():
    extractor = LLMClaimExtractor(FakeLLM())

    claims = await extractor.extract(
        "The benchmark achieved 95 percent accuracy."
    )

    assert len(claims) == 2

    assert claims[0].claim_type == "quantitative"
    assert claims[0].importance == "high"

    assert claims[1].claim_type == "comparative"
    assert claims[1].importance == "medium"


@pytest.mark.asyncio
async def test_llm_claim_extractor_handles_empty_text():
    extractor = LLMClaimExtractor(FakeLLM())

    claims = await extractor.extract("")

    assert claims == []


@pytest.mark.asyncio
async def test_llm_claim_extractor_rejects_invalid_json():
    extractor = LLMClaimExtractor(InvalidJSONLLM())

    with pytest.raises(ValueError, match="invalid JSON"):
        await extractor.extract("Some research text.")


def test_fake_llm_matches_provider_protocol():
    assert isinstance(FakeLLM(), LLMProvider)