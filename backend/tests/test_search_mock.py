"""Tests for mock search provider."""

from __future__ import annotations

import pytest

from app.providers.search.mock import MockSearchProvider


@pytest.mark.asyncio
async def test_mock_search_is_deterministic() -> None:
    provider = MockSearchProvider()
    first = await provider.search("climate change impacts", max_results=3)
    second = await provider.search("climate change impacts", max_results=3)
    assert first == second


@pytest.mark.asyncio
async def test_mock_search_respects_max_results() -> None:
    provider = MockSearchProvider()
    results = await provider.search("renewable energy", max_results=2)
    assert len(results) == 2
    assert results[0].score >= results[1].score


@pytest.mark.asyncio
async def test_mock_search_differs_by_query() -> None:
    provider = MockSearchProvider()
    results_a = await provider.search("query alpha")
    results_b = await provider.search("query beta")
    assert results_a[0].url != results_b[0].url
