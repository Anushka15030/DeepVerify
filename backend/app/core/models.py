"""Core Pydantic models for DeepVerify research workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

SubtaskStatus = Literal["pending", "in_progress", "completed", "failed", "skipped"]
SubtaskPurpose = Literal["consensus", "empirical", "counterarguments"]
ClaimVerdict = Literal["supported", "refuted", "inconclusive", "unverifiable"]
AgentEventType = Literal[
    "plan_created",
    "subtask_started",
    "subtask_completed",
    "search_started",
    "search_completed",
    "claims_extracted",
    "claim_checked",
    "error",
    "run_completed",
]


class ResearchSubtask(BaseModel):
    """A single research subtask within a plan."""

    id: str
    query: str
    title: str | None = None
    purpose: SubtaskPurpose | None = None
    status: SubtaskStatus = "pending"
    priority: int = Field(default=1, ge=1, le=10)
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("id", "query")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class ResearchPlan(BaseModel):
    """Structured plan decomposing a research topic into subtasks."""

    topic: str
    subtasks: list[ResearchSubtask] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("topic must not be blank")
        return value


class SourceMetadata(BaseModel):
    """Metadata for an external information source."""

    url: str
    title: str
    snippet: str
    retrieved_at: datetime
    provider: str

    @field_validator("url", "title", "provider")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class Evidence(BaseModel):
    """Evidence supporting or refuting a claim."""

    excerpt: str
    sources: list[SourceMetadata] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("excerpt")
    @classmethod
    def excerpt_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("excerpt must not be blank")
        return value


class ClaimCheck(BaseModel):
    """Result of verifying a factual claim."""

    claim: str
    verdict: ClaimVerdict
    evidence: list[Evidence] = Field(default_factory=list)
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""

    @field_validator("claim")
    @classmethod
    def claim_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("claim must not be blank")
        return value


class AgentEvent(BaseModel):
    """SSE-ready event envelope for agent activity streaming."""

    type: AgentEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_id: str

    @field_validator("run_id")
    @classmethod
    def run_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("run_id must not be blank")
        return value
