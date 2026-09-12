"""Tavily web search provider."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.providers.search.base import SearchResponse, SearchResult


class TavilySearchProvider:
    """Search provider backed by the Tavily Search API."""

    provider_name = "tavily"
    base_url = "https://api.tavily.com/search"

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Tavily API key must not be blank")

        self.api_key = api_key
        self.timeout = timeout

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> SearchResponse:
        """Run a Tavily search and normalize the response."""

        if not query.strip():
            return SearchResponse(query=query, results=[])

        payload = {
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": False,
            "include_raw_content": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers=headers,
            )

        response.raise_for_status()
        data = response.json()

        results: list[SearchResult] = []

        for item in data.get("results", []):
            content = (
                item.get("raw_content")
                or item.get("content")
                or ""
            )

            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    content=content,
                    provider=self.provider_name,
                    retrieved_at=datetime.now(timezone.utc),
                )
            )

        return SearchResponse(
            query=query,
            results=results,
        )