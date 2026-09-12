"""Deterministic mock search provider."""

from __future__ import annotations

import hashlib

from app.providers.search.base import SearchResult


class MockSearchProvider:
    """Returns deterministic search results based on query hash."""

    provider_name: str = "mock"

    @staticmethod
    def _query_digest(query: str) -> str:
        return hashlib.sha256(query.encode("utf-8")).hexdigest()

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if max_results < 1:
            return []

        digest = self._query_digest(query)
        count = min(max_results, 10)

        results: list[SearchResult] = []
        for index in range(count):
            segment = digest[index * 2 : index * 2 + 8]
            results.append(
                SearchResult(
                    title=f"Mock result {index + 1}: {query[:40]}",
                    url=f"https://mock.example/{digest[:8]}/{index}",
                    snippet=f"Deterministic snippet [{segment}] for query.",
                    score=round(1.0 - (index * 0.1), 2),
                )
            )
        return results
