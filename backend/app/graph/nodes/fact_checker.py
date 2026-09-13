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
        #
        # First pass:
        #     Check every claim.
        #
        # Revision pass:
        #     Check only claims whose latest grounding score
        #     is below the configured threshold.
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

        # ---------------------------------------------------------
        # If there are no weak claims left, keep the existing
        # grounding score and do not create duplicate checks.
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
        # Fact-check the selected claims.
        # ---------------------------------------------------------

        mode = "llm"
        claim_checks = []

        try:
            checker = LLMFactChecker(llm)

            for claim in claims_to_check:
                result = await checker.check_claim(
                    claim,
                    state.evidence,
                )
                claim_checks.append(result)

        except Exception:
            mode = "deterministic_fallback"

            fallback_checker = FactChecker()

            claim_checks = [
                fallback_checker.check_claim(
                    claim,
                    state.evidence,
                )
                for claim in claims_to_check
            ]

        # ---------------------------------------------------------
        # Merge the new checks with previous checks.
        #
        # The state stores claim_checks as an append-only list,
        # so we build a "latest result per claim" view here.
        # ---------------------------------------------------------

        latest_checks = {
            check.claim: check
            for check in state.claim_checks
        }

        for check in claim_checks:
            latest_checks[check.claim] = check

        # ---------------------------------------------------------
        # Calculate the overall grounding score using the latest
        # result for every claim.
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