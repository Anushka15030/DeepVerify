"""Tests for LLM fact-checker verdict normalization and defensive parsing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agents.llm_fact_checker import (
    LLMFactChecker,
    _coerce_grounding_score,
    _normalize_verdict,
)
from app.core.models import Evidence, SourceMetadata


class VerdictResponder:
    """Fake LLM that returns a fixed verdict dict."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        import json

        return json.dumps(self._payload)


def make_evidence(text: str = "Some factual evidence.") -> Evidence:
    source = SourceMetadata(
        url="https://example.com",
        title="Example Source",
        snippet=text,
        provider="test",
        retrieved_at=datetime.now(timezone.utc),
    )
    return Evidence(excerpt=text, sources=[source], confidence=0.9)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("supported", "supported"),
        ("contradicted", "refuted"),
        ("Contradicted", "refuted"),
        ("CONTRADICTED", "refuted"),
        ("contradicts", "refuted"),
        ("false", "refuted"),
        ("unverified", "unverifiable"),
        ("cannot_verify", "unverifiable"),
        ("no evidence", "unverifiable"),
        ("ambiguous", "inconclusive"),
        ("mixed", "inconclusive"),
        ("refuted", "refuted"),
        ("unverifiable", "unverifiable"),
        ("inconclusive", "inconclusive"),
    ],
)
def test_normalize_verdict_maps_synonyms(raw: str, expected: str) -> None:
    assert _normalize_verdict(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["", "   ", None, "who knows what", "idk", 42],
)
def test_normalize_verdict_rejects_unknown(raw) -> None:
    with pytest.raises(ValueError, match="verdict"):
        _normalize_verdict(raw)


def test_coerce_grounding_score_clamps_high() -> None:
    assert _coerce_grounding_score(1.7) == 1.0
    assert _coerce_grounding_score(1.0) == 1.0


def test_coerce_grounding_score_clamps_low() -> None:
    assert _coerce_grounding_score(-0.3) == 0.0
    assert _coerce_grounding_score(0.0) == 0.0


def test_coerce_grounding_score_in_range() -> None:
    assert _coerce_grounding_score(0.55) == 0.55


def test_coerce_grounding_score_handles_bad_types() -> None:
    assert _coerce_grounding_score(None) == 0.0
    assert _coerce_grounding_score("garbage") == 0.0
    assert _coerce_grounding_score(True) == 0.0


@pytest.mark.asyncio
async def test_check_claim_accepts_out_of_range_score() -> None:
    """A score above 1.0 must be clamped, not crash the workflow."""
    checker = LLMFactChecker(
        VerdictResponder(
            {
                "verdict": "supported",
                "grounding_score": 2.5,
                "explanation": "very confident",
                "evidence_indices": [0],
            }
        )
    )
    result = await checker.check_claim("claim", [make_evidence()])
    assert result.verdict == "supported"
    assert result.grounding_score == 1.0


@pytest.mark.asyncio
async def test_check_claim_normalizes_legacy_contradicted() -> None:
    """The model drifted from 'refuted' to 'contradicted'; must map to refuted."""
    checker = LLMFactChecker(
        VerdictResponder(
            {
                "verdict": "contradicted",
                "grounding_score": 0.9,
                "explanation": "evidence conflicts",
                "evidence_indices": [0],
            }
        )
    )
    result = await checker.check_claim("claim", [make_evidence()])
    assert result.verdict == "refuted"
    assert result.grounding_score == 0.9


@pytest.mark.asyncio
async def test_check_claim_rejects_unknown_verdict() -> None:
    checker = LLMFactChecker(
        VerdictResponder(
            {
                "verdict": "not-a-real-verdict",
                "grounding_score": 0.5,
                "explanation": "",
                "evidence_indices": [],
            }
        )
    )
    with pytest.raises(ValueError, match="unknown verdict"):
        await checker.check_claim("claim", [make_evidence()])


@pytest.mark.asyncio
async def test_check_claim_missing_score_defaults_to_zero() -> None:
    checker = LLMFactChecker(
        VerdictResponder(
            {
                "verdict": "inconclusive",
                "explanation": "no score given",
                "evidence_indices": [],
            }
        )
    )
    result = await checker.check_claim("claim", [make_evidence()])
    assert result.verdict == "inconclusive"
    assert result.grounding_score == 0.0


@pytest.mark.asyncio
async def test_check_claim_uses_only_valid_evidence_indices() -> None:
    checker = LLMFactChecker(
        VerdictResponder(
            {
                "verdict": "supported",
                "grounding_score": 0.9,
                "explanation": "ok",
                "evidence_indices": [0, 5, -1, "bad"],
            }
        )
    )
    evidence = [make_evidence("first"), make_evidence("second")]
    result = await checker.check_claim("claim", evidence)
    assert len(result.evidence) == 1
    assert result.evidence[0].excerpt == "first"


@pytest.mark.asyncio
async def test_check_claim_prompt_uses_refuted_vocabulary() -> None:
    """The system prompt must instruct 'refuted', never the unmapped 'contradicted'."""

    class CapturingLLM:
        def __init__(self) -> None:
            self.captured: str | None = None

        async def complete(self, prompt: str, system: str | None = None) -> str:
            self.captured = system
            return '{"verdict": "supported", "grounding_score": 1.0, "explanation": "", "evidence_indices": []}'

    raw = CapturingLLM()
    checker = LLMFactChecker(raw)
    await checker.check_claim("claim", [make_evidence()])

    assert raw.captured is not None
    assert "refuted" in raw.captured
    assert "contradicted" not in raw.captured