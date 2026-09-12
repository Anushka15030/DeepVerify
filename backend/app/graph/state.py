"""Typed graph state for DeepVerify LangGraph workflows."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from pydantic import BaseModel, Field

from app.core.models import AgentEvent, ClaimCheck, Evidence, ResearchPlan


class DeepVerifyState(BaseModel):
    """Complete state for a DeepVerify research run (public API return type)."""

    run_id: str
    original_question: str
    research_plan: ResearchPlan | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    draft: str | None = None
    claims: list[str] = Field(default_factory=list)
    claim_checks: list[ClaimCheck] = Field(default_factory=list)
    grounding_score: float | None = None
    revision_count: int = 0
    agent_events: list[AgentEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def merge_agent_events(
    left: list[AgentEvent], right: list[AgentEvent]
) -> list[AgentEvent]:
    """Reducer: append agent events from parallel branches."""
    return left + right


def merge_evidence(left: list[Evidence], right: list[Evidence]) -> list[Evidence]:
    """Reducer: append evidence from parallel branches."""
    return left + right


def merge_claim_checks(
    left: list[ClaimCheck], right: list[ClaimCheck]
) -> list[ClaimCheck]:
    """Reducer: append claim checks from parallel branches."""
    return left + right


def merge_claims(left: list[str], right: list[str]) -> list[str]:
    """Reducer: append claims from parallel branches."""
    return left + right


def merge_errors(left: list[str], right: list[str]) -> list[str]:
    """Reducer: append errors from parallel branches."""
    return left + right


class DeepVerifyGraphState(BaseModel):
    """LangGraph-compatible state with reducers for parallel node updates."""

    run_id: str
    original_question: str
    research_plan: ResearchPlan | None = None
    evidence: Annotated[list[Evidence], merge_evidence] = Field(default_factory=list)
    draft: str | None = None
    claims: Annotated[list[str], merge_claims] = Field(default_factory=list)
    claim_checks: Annotated[list[ClaimCheck], merge_claim_checks] = Field(
        default_factory=list
    )
    grounding_score: float | None = None
    revision_count: int = 0
    agent_events: Annotated[list[AgentEvent], merge_agent_events] = Field(
        default_factory=list
    )
    errors: Annotated[list[str], merge_errors] = Field(default_factory=list)

    def to_deep_verify_state(self) -> DeepVerifyState:
        """Convert graph state to the public DeepVerifyState model."""
        return DeepVerifyState.model_validate(self.model_dump())


def initial_graph_state(question: str, run_id: str) -> dict[str, Any]:
    """Build the initial state dict for graph invocation."""
    return {
        "run_id": run_id,
        "original_question": question,
        "research_plan": None,
        "evidence": [],
        "draft": None,
        "claims": [],
        "claim_checks": [],
        "grounding_score": None,
        "revision_count": 0,
        "agent_events": [],
        "errors": [],
    }
