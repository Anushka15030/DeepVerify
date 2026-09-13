"""Tests for core Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.core.models import (
    AgentEvent,
    ClaimCheck,
    Evidence,
    ExtractedClaim,
    ResearchPlan,
    ResearchSubtask,
    SourceMetadata,
)


def test_research_subtask_valid() -> None:
    subtask = ResearchSubtask(id="st-1", query="What is quantum computing?")
    assert subtask.status == "pending"
    assert subtask.priority == 1


def test_research_subtask_rejects_blank_fields() -> None:
    with pytest.raises(ValidationError):
        ResearchSubtask(id="  ", query="valid")


def test_research_plan_with_subtasks() -> None:
    plan = ResearchPlan(
        topic="AI safety",
        subtasks=[ResearchSubtask(id="1", query="recent papers")],
        metadata={"version": 1},
    )
    assert plan.topic == "AI safety"
    assert len(plan.subtasks) == 1
    assert plan.metadata["version"] == 1


def test_source_metadata_valid() -> None:
    source = SourceMetadata(
        url="https://example.com/article",
        title="Example Article",
        snippet="A short summary.",
        retrieved_at=datetime.now(timezone.utc),
        provider="mock",
    )
    assert source.provider == "mock"


def test_evidence_confidence_bounds() -> None:
    with pytest.raises(ValidationError):
        Evidence(excerpt="text", confidence=1.5)


def test_claim_check_valid() -> None:
    claim = ClaimCheck(claim="Earth is round.", verdict="supported")
    assert claim.verdict == "supported"
    assert claim.evidence == []


def test_claim_check_invalid_verdict() -> None:
    with pytest.raises(ValidationError):
        ClaimCheck(claim="test", verdict="maybe")  # type: ignore[arg-type]


def test_agent_event_defaults_timestamp() -> None:
    event = AgentEvent(type="plan_created", payload={"topic": "x"}, run_id="run-1")
    assert event.timestamp.tzinfo is not None
    assert event.payload["topic"] == "x"


def test_agent_event_requires_run_id() -> None:
    with pytest.raises(ValidationError):
        AgentEvent(type="error", payload={}, run_id="  ")

def test_extracted_claim_valid():
    claim = ExtractedClaim(
        claim="India installed 12 GW of solar capacity.",
        claim_type="quantitative",
        importance="high",
    )

    assert claim.claim == "India installed 12 GW of solar capacity."
    assert claim.claim_type == "quantitative"
    assert claim.importance == "high"


def test_extracted_claim_rejects_blank_claim():
    with pytest.raises(ValueError):
        ExtractedClaim(
            claim="   ",
            claim_type="factual",
            importance="medium",
        )
