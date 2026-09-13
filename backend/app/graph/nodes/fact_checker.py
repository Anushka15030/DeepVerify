"""Fact-checking graph node."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.fact_checker import FactChecker
from app.agents.llm_fact_checker import LLMFactChecker
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


def make_fact_checker_node(llm: LLMProvider):
    async def fact_checker_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:
        run_id = state.run_id

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

        mode = "llm"
        claim_checks = []

        try:
            checker = LLMFactChecker(llm)

            for claim in state.claims:
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
                for claim in state.claims
            ]

        grounding_score = (
            sum(check.grounding_score for check in claim_checks)
            / len(claim_checks)
            if claim_checks
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
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "claim_checks": claim_checks,
            "grounding_score": grounding_score,
            "agent_events": [event],
        }

    return fact_checker_node