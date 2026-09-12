"""Search provider protocol and result model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single web search result."""

    title: str
    url: str
    snippet: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for async web search providers."""

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Execute a search query and return ranked results."""
        ...
