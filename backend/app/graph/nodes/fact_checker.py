"""Fact-checking graph node."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.agents.fact_checker import FactChecker
from app.agents.llm_fact_checker import LLMFactChecker
from app.core.config import get_settings
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


# Cost-control limits.
MAX_CLAIMS_PER_PASS = 6
MAX_EVIDENCE_PER_CLAIM = 4
MAX_EXCERPT_CHARS = 1000

_STOP_WORDS = {
    "about",
    "after",
    "also",
    "because",
    "being",
    "between",
    "could",
    "does",
    "from",
    "have",
    "into",
    "more",
    "other",
    "should",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "using",
    "were",
    "which",
    "with",
}


def _tokenize(text: str) -> set[str]:
    """Normalize text into meaningful comparison tokens."""

    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) >= 4 and token not in _STOP_WORDS
    }


def _select_evidence_for_claim(
    claim: str,
    evidence: list,
) -> list:
    """Select the strongest evidence matches for a claim."""

    claim_tokens = _tokenize(claim)

    if not claim_tokens:
        return []

    scored: list[tuple[float, Any]] = []

    for item in evidence:
        excerpt = item.excerpt.strip()

        if not excerpt:
            continue

        evidence_tokens = _tokenize(excerpt)

        if not evidence_tokens:
            continue

        overlap = claim_tokens & evidence_tokens

        if not overlap:
            continue

        # Fraction of claim concepts appearing in the evidence.
        relevance = len(overlap) / len(claim_tokens)

        # Give a small boost to higher-confidence evidence.
        score = (
            relevance * 0.7
            + item.confidence * 0.3
        )

        scored.append((score, item))

    scored.sort(
        key=lambda pair: pair[0],
        reverse=True,
    )

    return [
        item
        for _, item in scored
    ][:MAX_EVIDENCE_PER_CLAIM]


def make_fact_checker_node(llm: LLMProvider):

    async def fact_checker_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:

        run_id = state.run_id
        settings = get_settings()

        if not state.claims:
            event = AgentEvent(
                type="claim_checked",
                run_id=run_id,
                payload={
                    "agent": "fact_checker",
                    "claims_checked": 0,
                    "grounding_score": 0.0,
                    "mode": "none",
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "claim_checks": [],
                "grounding_score": 0.0,
                "agent_events": [event],
            }

        if state.revision_count == 0:
            claims_to_check = state.claims
        else:
            latest_checks = {
                check.claim: check
                for check in state.claim_checks
            }

            claims_to_check = [
                claim
                for claim in state.claims
                if (
                    claim not in latest_checks
                    or latest_checks[claim].grounding_score
                    < settings.grounding_pass_threshold
                )
            ]

        claims_to_check = claims_to_check[:MAX_CLAIMS_PER_PASS]

        if not claims_to_check:
            latest_checks = {
                check.claim: check
                for check in state.claim_checks
            }

            grounding_score = (
                sum(
                    check.grounding_score
                    for check in latest_checks.values()
                )
                / len(latest_checks)
                if latest_checks
                else 0.0
            )

            event = AgentEvent(
                type="claim_checked",
                run_id=run_id,
                payload={
                    "agent": "fact_checker",
                    "claims_checked": 0,
                    "grounding_score": grounding_score,
                    "mode": "no_revision_needed",
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "claim_checks": [],
                "grounding_score": grounding_score,
                "agent_events": [event],
            }

        mode = "llm"
        claim_checks = []

        try:
            checker = LLMFactChecker(llm)

            for claim in claims_to_check:
                relevant_evidence = _select_evidence_for_claim(
                    claim,
                    state.evidence,
                )

                compact_evidence = [
                    evidence.model_copy(
                        update={
                            "excerpt": evidence.excerpt.strip()[
                                :MAX_EXCERPT_CHARS
                            ]
                        }
                    )
                    for evidence in relevant_evidence
                ]

                result = await checker.check_claim(
                    claim,
                    compact_evidence,
                )

                claim_checks.append(result)

        except Exception:
            mode = "deterministic_fallback"

            fallback_checker = FactChecker()
            claim_checks = []

            for claim in claims_to_check:
                relevant_evidence = _select_evidence_for_claim(
                    claim,
                    state.evidence,
                )

                result = fallback_checker.check_claim(
                    claim,
                    relevant_evidence,
                )

                claim_checks.append(result)

        latest_checks = {
            check.claim: check
            for check in state.claim_checks
        }

        for check in claim_checks:
            latest_checks[check.claim] = check

        grounding_score = (
            sum(
                check.grounding_score
                for check in latest_checks.values()
            )
            / len(latest_checks)
            if latest_checks
            else 0.0
        )

        event = AgentEvent(
            type="claim_checked",
            run_id=run_id,
            payload={
                "agent": "fact_checker",
                "claims_checked": len(claim_checks),
                "grounding_score": grounding_score,
                "mode": mode,
                "revision_count": state.revision_count,
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "claim_checks": claim_checks,
            "grounding_score": grounding_score,
            "agent_events": [event],
        }

    return fact_checker_node