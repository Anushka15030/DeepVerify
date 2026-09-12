"""Tests for the search-provider abstraction and mock provider."""

from __future__ import annotations

import pytest

from app.providers.search import (
    MockSearchProvider,
    SearchResponse,
    SearchResult,
)


@pytest.mark.asyncio
async def test_mock_search_returns_search_response() -> None:
    provider = MockSearchProvider()

    response = await provider.search("climate change", max_results=5)

    assert isinstance(response, SearchResponse)
    assert response.query == "climate change"
    assert len(response.results) == 1


@pytest.mark.asyncio
async def test_mock_search_returns_normalized_result() -> None:
    provider = MockSearchProvider()

    response = await provider.search("DeepVerify")

    result = response.results[0]

    assert isinstance(result, SearchResult)
    assert result.title
    assert result.url
    assert result.provider == "mock"
    assert result.snippet
    assert result.content
    assert result.retrieved_at is not None


@pytest.mark.asyncio
async def test_mock_search_respects_max_results() -> None:
    results = [
        SearchResult(
            title=f"Result {index}",
            url=f"https://example.com/{index}",
            provider="mock",
        )
        for index in range(5)
    ]

    provider = MockSearchProvider(results=results)

    response = await provider.search("test", max_results=2)

    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_mock_search_empty_query_returns_no_results() -> None:
    provider = MockSearchProvider()

    response = await provider.search("   ")

    assert response.query == "   "
    assert response.results == []


@pytest.mark.asyncio
async def test_mock_search_is_deterministic() -> None:
    provider = MockSearchProvider()

    first = await provider.search("same query")
    second = await provider.search("same query")

    assert first.query == second.query
    assert len(first.results) == len(second.results)

    assert first.results[0].title == second.results[0].title
    assert first.results[0].url == second.results[0].url
    assert first.results[0].content == second.results[0].content
    assert first.results[0].provider == second.results[0].provider