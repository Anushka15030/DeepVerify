"""Claim extractor graph node."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.claim_extractor import ClaimExtractor
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState


def claim_extractor_node(
    state: DeepVerifyGraphState,
) -> dict[str, Any]:
    """Extract factual claims from the available research evidence."""

    run_id = state.run_id

    extractor = ClaimExtractor()

    research_text = "\n".join(
        evidence.excerpt
        for evidence in state.evidence
        if evidence.excerpt.strip()
    )

    claims = extractor.extract(research_text)

    event = AgentEvent(
        type="claims_extracted",
        run_id=run_id,
        payload={
            "agent": "claim_extractor",
            "claims_count": len(claims),
        },
        timestamp=datetime.now(timezone.utc),
    )

    return {
        "claims": claims,
        "agent_events": [event],
    }