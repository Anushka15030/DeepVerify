"""Fact-checking graph node."""

from __future__ import annotations

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


def _select_evidence_for_claim(claim: str, evidence: list) -> list:
    """Select a small evidence subset that is most relevant to a claim."""

    claim_tokens = {
        token.lower()
        for token in claim.split()
        if len(token) >= 4
    }

    scored: list[tuple[int, Any]] = []

    for item in evidence:
        excerpt = item.excerpt.strip()

        if not excerpt:
            continue

        excerpt_tokens = {
            token.lower()
            for token in excerpt.split()
            if len(token) >= 4
        }

        overlap = len(claim_tokens & excerpt_tokens)

        scored.append((overlap, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    selected = [
        item
        for _, item in scored[:MAX_EVIDENCE_PER_CLAIM]
    ]

    return selected


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

        # ---------------------------------------------------------
        # Decide which claims need to be checked.
        # ---------------------------------------------------------

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

        # Hard limit to prevent unexpectedly expensive LLM runs.
        claims_to_check = claims_to_check[:MAX_CLAIMS_PER_PASS]

        # ---------------------------------------------------------
        # If there are no weak claims left, keep the existing
        # grounding score.
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Fact-check selected claims using only relevant evidence.
        # ---------------------------------------------------------

        mode = "llm"
        claim_checks = []

        try:
            checker = LLMFactChecker(llm)

            for claim in claims_to_check:
                relevant_evidence = _select_evidence_for_claim(
                    claim,
                    state.evidence,
                )

                # Trim excerpts before sending them to the LLM.
                compact_evidence = []

                for evidence in relevant_evidence:
                    evidence_copy = evidence.model_copy(
                        update={
                            "excerpt": evidence.excerpt.strip()[
                                :MAX_EXCERPT_CHARS
                            ]
                        }
                    )

                    compact_evidence.append(evidence_copy)

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

                claim_checks.append(
                    fallback_checker.check_claim(
                        claim,
                        relevant_evidence,
                    )
                )

        # ---------------------------------------------------------
        # Merge new checks with previous checks.
        # ---------------------------------------------------------

        latest_checks = {
            check.claim: check
            for check in state.claim_checks
        }

        for check in claim_checks:
            latest_checks[check.claim] = check

        # ---------------------------------------------------------
        # Calculate overall grounding score.
        # ---------------------------------------------------------

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