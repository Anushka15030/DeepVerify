"""Claim extractor graph node."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.agents.claim_extractor import ClaimExtractor
from app.agents.llm_claim_extractor import LLMClaimExtractor
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


def make_claim_extractor_node(llm: LLMProvider):
    """Create a claim extractor node using an injected LLM."""

    async def claim_extractor_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:
        """Extract structured claims using the LLM with deterministic fallback."""

        run_id = state.run_id

        research_text = "\n".join(
            evidence.excerpt
            for evidence in state.evidence
            if evidence.excerpt.strip()
        )

        if not research_text:
            event = AgentEvent(
                type="claims_extracted",
                run_id=run_id,
                payload={
                    "agent": "claim_extractor",
                    "claims_count": 0,
                    "mode": "none",
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "claims": [],
                "agent_events": [event],
            }

        mode = "llm"

        try:
            llm_extractor = LLMClaimExtractor(llm)
            extracted_claims = await llm_extractor.extract(
                research_text
            )

            claims = [item.claim for item in extracted_claims]

        except Exception:
            mode = "deterministic_fallback"

            fallback_extractor = ClaimExtractor()
            claims = fallback_extractor.extract(research_text)

        event = AgentEvent(
            type="claims_extracted",
            run_id=run_id,
            payload={
                "agent": "claim_extractor",
                "claims_count": len(claims),
                "mode": mode,
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "claims": claims,
            "agent_events": [event],
        }

    return claim_extractor_node