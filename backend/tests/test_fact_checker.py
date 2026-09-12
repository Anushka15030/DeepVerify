"""Tests for the DeepVerify fact checker."""

from datetime import datetime, timezone

import pytest

from app.agents.fact_checker import FactChecker
from app.core.models import Evidence, SourceMetadata


def make_evidence(
    excerpt: str,
    confidence: float = 0.8,
) -> Evidence:
    """Create deterministic test evidence."""

    source = SourceMetadata(
        url="https://example.com/source",
        title="Test Source",
        snippet="Test source snippet",
        retrieved_at=datetime.now(timezone.utc),
        provider="test",
    )

    return Evidence(
        excerpt=excerpt,
        sources=[source],
        confidence=confidence,
    )


def test_fact_checker_returns_unverifiable_without_evidence() -> None:
    checker = FactChecker()

    result = checker.check_claim(
        "AI systems can hallucinate.",
        [],
    )

    assert result.claim == "AI systems can hallucinate."
    assert result.verdict == "unverifiable"
    assert result.grounding_score == 0.0
    assert result.evidence == []


def test_fact_checker_returns_inconclusive_with_evidence() -> None:
    checker = FactChecker()

    evidence = [
        make_evidence(
            "Retrieval augmented generation can reduce hallucinations.",
            confidence=0.8,
        )
    ]

    result = checker.check_claim(
        "RAG can reduce hallucinations.",
        evidence,
    )

    assert result.verdict == "inconclusive"
    assert result.grounding_score == 0.8
    assert len(result.evidence) == 1


def test_fact_checker_uses_average_evidence_confidence() -> None:
    checker = FactChecker()

    evidence = [
        make_evidence("First evidence.", confidence=0.8),
        make_evidence("Second evidence.", confidence=0.6),
    ]

    result = checker.check_claim(
        "A test claim.",
        evidence,
    )

    assert result.grounding_score == pytest.approx(0.7)


def test_fact_checker_rejects_blank_claim() -> None:
    checker = FactChecker()

    with pytest.raises(ValueError, match="claim must not be blank"):
        checker.check_claim("   ", [])