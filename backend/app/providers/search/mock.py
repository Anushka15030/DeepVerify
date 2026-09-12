"""Deterministic mock search provider for tests and local development."""

from __future__ import annotations

from datetime import datetime, timezone

from app.providers.search.base import SearchProvider, SearchResponse, SearchResult


class MockSearchProvider:
    """Deterministic search provider used for testing."""

    provider_name = "mock"

    def __init__(self, results: list[SearchResult] | None = None) -> None:
        self._results = results or [
            SearchResult(
                title="DeepVerify Mock Source",
                url="https://example.com/deepverify",
                snippet="A deterministic mock search result.",
                content=(
                    "This is mock content used to test the DeepVerify "
                    "search-provider contract."
                ),
                provider=self.provider_name,
                retrieved_at=datetime.now(timezone.utc),
            )
        ]

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> SearchResponse:
        """Return deterministic results without making a network request."""

        if not query.strip():
            return SearchResponse(query=query, results=[])

        limited_results = self._results[:max_results]

        return SearchResponse(
            query=query,
            results=limited_results,
        )