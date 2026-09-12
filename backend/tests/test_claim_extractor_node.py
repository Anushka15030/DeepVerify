from datetime import datetime, timezone
from app.core.models import Evidence, SourceMetadata
from app.graph.nodes.claim_extractor import claim_extractor_node
from app.graph.state import DeepVerifyGraphState


def make_state(text: str) -> DeepVerifyGraphState:
    source = SourceMetadata(
    url="https://example.com",
    title="Example Source",
    snippet=text,
    provider="test",
    retrieved_at=datetime.now(timezone.utc),
    )

    evidence = Evidence(
        excerpt=text,
        sources=[source],
        confidence=0.8,
    )

    return DeepVerifyGraphState(
        run_id="test-run",
        original_question="Test question",
        evidence=[evidence],
    )


def test_claim_extractor_node_extracts_claims():
    state = make_state(
        "Solar capacity increased by 25% in 2025. "
        "India added 12 GW of new capacity."
    )

    result = claim_extractor_node(state)

    assert result["claims"] == [
        "Solar capacity increased by 25% in 2025.",
        "India added 12 GW of new capacity.",
    ]


def test_claim_extractor_node_emits_event():
    state = make_state(
        "Solar capacity increased by 25% in 2025."
    )

    result = claim_extractor_node(state)

    assert len(result["agent_events"]) == 1
    assert result["agent_events"][0].type == "claims_extracted"


def test_claim_extractor_node_handles_no_evidence():
    state = DeepVerifyGraphState(
        run_id="test-run",
        original_question="Test question",
    )

    result = claim_extractor_node(state)

    assert result["claims"] == []
    assert result["agent_events"][0].payload["claims_count"] == 0