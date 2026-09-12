"""Fact-checker graph node."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.fact_checker import FactChecker
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState


def fact_checker_node(
    state: DeepVerifyGraphState,
) -> dict[str, Any]:
    """Check available claims against collected evidence."""

    run_id = state.run_id
    checker = FactChecker()

    claim_checks = [
        checker.check_claim(claim, state.evidence)
        for claim in state.claims
    ]

    if claim_checks:
        grounding_score = sum(
            check.grounding_score for check in claim_checks
        ) / len(claim_checks)
    else:
        grounding_score = 0.0

    event = AgentEvent(
        type="claim_checked",
        run_id=run_id,
        payload={
            "agent": "fact_checker",
            "claims_checked": len(claim_checks),
            "grounding_score": grounding_score,
        },
        timestamp=datetime.now(timezone.utc),
    )

    return {
        "claim_checks": claim_checks,
        "grounding_score": grounding_score,
        "agent_events": [event],
    }