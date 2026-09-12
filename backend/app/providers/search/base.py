"""Search provider interfaces and provider-independent result models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A provider-independent web search result."""

    title: str
    url: str
    snippet: str = ""
    content: str = ""
    provider: str
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class SearchResponse(BaseModel):
    """A normalized response returned by a search provider."""

    query: str
    results: list[SearchResult] = Field(default_factory=list)


@runtime_checkable
class SearchProvider(Protocol):
    """Interface implemented by all web search providers."""

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> SearchResponse:
        """Search the web and return normalized results."""
        ...