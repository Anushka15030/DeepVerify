"""Fact-checking graph node."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.agents.fact_checker import FactChecker
from app.agents.llm_fact_checker import LLMFactChecker
from app.core.config import get_settings
from app.core.models import AgentEvent, ClaimCheck
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

        # Ignore evidence with only a single coincidental keyword.
        if len(overlap) < 2:
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

            claim_checks = []

            for claim in claims_to_check:
                relevant_evidence = _select_evidence_for_claim(
                    claim,
                    state.evidence,
                )

                result = _fallback_fact_check(
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

def _fallback_fact_check(
    claim: str,
    evidence_items: list,
) -> ClaimCheck:
    """Deterministic evidence-aware fallback used when the LLM is unavailable.

    This is deliberately conservative:
    - strong semantic/lexical overlap can support a claim;
    - explicit polarity mismatch can refute a claim;
    - weak or ambiguous overlap remains unverifiable/inconclusive.

    It does not treat a shared keyword as proof.
    """

    if not claim or not claim.strip():
        return ClaimCheck(
            claim=claim,
            verdict="unverifiable",
            grounding_score=0.0,
            explanation="The claim is empty and cannot be verified.",
            evidence=[],
            verification_method="deterministic_fallback",
        )

    if not evidence_items:
        return ClaimCheck(
            claim=claim,
            verdict="unverifiable",
            grounding_score=0.0,
            explanation="No relevant evidence was retrieved for this claim.",
            evidence=[],
            verification_method="deterministic_fallback",
        )

    claim_tokens = _tokenize(claim)

    if not claim_tokens:
        return ClaimCheck(
            claim=claim,
            verdict="unverifiable",
            grounding_score=0.0,
            explanation=(
                "The claim does not contain enough meaningful terms "
                "for deterministic verification."
            ),
            evidence=[],
            verification_method="deterministic_fallback",
        )

    scored: list[tuple[float, int, Any, set[str]]] = []

    for index, item in enumerate(evidence_items):
        excerpt = (getattr(item, "excerpt", "") or "").strip()

        if not excerpt:
            continue

        evidence_tokens = _tokenize(excerpt)
        overlap = claim_tokens & evidence_tokens

        # Require at least two shared concepts so generic words do not
        # make unrelated evidence look relevant.
        if len(overlap) < 2:
            continue

        relevance = len(overlap) / len(claim_tokens)

        try:
            confidence = float(getattr(item, "confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))

        score = (relevance * 0.80) + (confidence * 0.20)

        scored.append((score, index, item, overlap))

    if not scored:
        return ClaimCheck(
            claim=claim,
            verdict="unverifiable",
            grounding_score=0.10,
            explanation=(
                "The retrieved evidence does not contain enough overlapping "
                "information to verify this claim."
            ),
            evidence=[],
            verification_method="deterministic_fallback",
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:MAX_EVIDENCE_PER_CLAIM]

    best_score, _, best_item, best_overlap = top[0]
    selected_evidence = [item for _, _, item, _ in top]

    # Detect explicit polarity mismatch only when the evidence is strongly
    # related to the claim. This handles cases such as:
    #
    # Claim:    "AI is fully capable of detecting new misinformation."
    # Evidence: "AI is not capable enough of detecting new misinformation."
    #
    # while avoiding the mistake of treating every word like "limitation"
    # as a contradiction.
    negation_terms = {
        "not",
        "never",
        "cannot",
        "can't",
        "unable",
        "fails",
        "failed",
        "lack",
        "lacks",
        "insufficient",
    }

    positive_capability_terms = {
        "capable",
        "detect",
        "detecting",
        "accurate",
        "reliable",
        "effective",
        "eliminate",
        "solves",
        "solved",
        "prevents",
        "prevent",
        "always",
        "fully",
        "complete",
        "complete",
    }

    claim_lower = claim.lower()
    claim_has_negation = bool(
        re.search(
            r"\b(?:not|never|cannot|can't|unable|lack|lacks|without)\b",
            claim_lower,
        )
    )

    polarity_refuted = False

    for _, _, item, overlap in top:
        evidence_text = (getattr(item, "excerpt", "") or "").lower()

        evidence_has_negation = bool(
            re.search(
                r"\b(?:not|never|cannot|can't|unable|lack|lacks|insufficient)\b",
                evidence_text,
            )
        )

        shared_capability = bool(
            overlap & positive_capability_terms
        )

        # A negative evidence statement about the same capability contradicts
        # a positive claim, and vice versa.
        if (
            len(overlap) >= 3
            and evidence_has_negation
            and not claim_has_negation
            and shared_capability
        ):
            polarity_refuted = True
            break

    if polarity_refuted:
        return ClaimCheck(
            claim=claim,
            verdict="refuted",
            grounding_score=round(min(best_score, 0.35), 2),
            explanation=(
                "Strongly related evidence was retrieved, but it explicitly "
                "states a limitation or inability that conflicts with the "
                "claim."
            ),
            evidence=selected_evidence,
            verification_method="deterministic_fallback",
        )

    # Strong direct grounding.
    if best_score >= 0.65:
        return ClaimCheck(
            claim=claim,
            verdict="supported",
            grounding_score=round(min(best_score, 0.95), 2),
            explanation=(
                "The retrieved evidence contains substantial overlap with "
                "the claim and directly addresses its subject."
            ),
            evidence=selected_evidence,
            verification_method="deterministic_fallback",
        )

    # Moderate overlap means the evidence is relevant, but deterministic
    # lexical matching cannot establish the claim confidently.
    if best_score >= 0.35:
        return ClaimCheck(
            claim=claim,
            verdict="inconclusive",
            grounding_score=round(best_score, 2),
            explanation=(
                "Relevant evidence was found, but the available text does "
                "not provide enough direct support for a confident verdict."
            ),
            evidence=selected_evidence,
            verification_method="deterministic_fallback",
        )

    return ClaimCheck(
        claim=claim,
        verdict="unverifiable",
        grounding_score=round(best_score, 2),
        explanation=(
            "The retrieved evidence is too weakly related to establish "
            "whether the claim is supported or refuted."
        ),
        evidence=selected_evidence,
        verification_method="deterministic_fallback",
    )

