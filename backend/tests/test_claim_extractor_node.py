from datetime import datetime, timezone

import pytest

from app.core.models import Evidence, SourceMetadata
from app.graph.nodes.claim_extractor import make_claim_extractor_node
from app.graph.state import DeepVerifyGraphState


class FakeLLM:
    """Deterministic fake LLM for node tests."""

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        return """
        [
            {
                "claim": "Solar capacity increased by 25% in 2025.",
                "claim_type": "quantitative",
                "importance": "high"
            },
            {
                "claim": "India added 12 GW of new capacity.",
                "claim_type": "quantitative",
                "importance": "high"
            }
        ]
        """


class FailingLLM:
    """Fake LLM that simulates an API failure."""

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        raise RuntimeError("LLM unavailable")


def make_state(*text: str) -> DeepVerifyGraphState:
    source = SourceMetadata(
        url="https://example.com",
        title="Example Source",
        snippet=" ".join(text),
        provider="test",
        retrieved_at=datetime.now(timezone.utc),
    )

    evidence = Evidence(
        excerpt=" ".join(text),
        sources=[source],
        confidence=0.8,
    )

    return DeepVerifyGraphState(
        run_id="test-run",
        original_question="Test question",
        evidence=[evidence],
    )


@pytest.mark.asyncio
async def test_claim_extractor_node_uses_llm():
    state = make_state(
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    )

    node = make_claim_extractor_node(FakeLLM())
    result = await node(state)

    assert result["claims"] == [
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    ]


@pytest.mark.asyncio
async def test_claim_extractor_node_emits_event():
    state = make_state(
        "Solar capacity increased by 25% in 2025."
    )

    node = make_claim_extractor_node(FakeLLM())
    result = await node(state)

    assert len(result["agent_events"]) == 1
    assert result["agent_events"][0].type == "claims_extracted"
    assert result["agent_events"][0].payload["mode"] == "llm"


@pytest.mark.asyncio
async def test_claim_extractor_node_handles_no_evidence():
    state = DeepVerifyGraphState(
        run_id="test-run",
        original_question="Test question",
    )

    node = make_claim_extractor_node(FakeLLM())
    result = await node(state)

    assert result["claims"] == []
    assert result["agent_events"][0].payload["claims_count"] == 0
    assert result["agent_events"][0].payload["mode"] == "none"


@pytest.mark.asyncio
async def test_claim_extractor_node_falls_back_when_llm_fails():
    state = make_state(
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    )

    node = make_claim_extractor_node(FailingLLM())
    result = await node(state)

    assert result["claims"] == [
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    ]

    assert result["agent_events"][0].payload["mode"] == (
        "deterministic_fallback"
    )