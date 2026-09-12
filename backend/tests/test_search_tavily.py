"""Tests for the Tavily search provider."""

from __future__ import annotations
import json
import httpx
import pytest

from app.providers.search.tavily import TavilySearchProvider


@pytest.mark.asyncio
async def test_tavily_search_normalizes_results() -> None:
    """Tavily results should be converted into DeepVerify SearchResult models."""

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.tavily.com/search"

        request_data = json.loads(request.content)

        assert request_data["query"] == "AI fact checking"
        assert request_data["max_results"] == 3
        assert request_data["search_depth"] == "advanced"
        assert request_data["include_raw_content"] is True

        assert request.headers["Authorization"] == "Bearer test-key"

        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "AI Fact Checking Research",
                        "url": "https://example.com/research",
                        "content": "A short search-result snippet.",
                        "raw_content": "Full article content used as evidence.",
                    },
                    {
                        "title": "Second Source",
                        "url": "https://example.com/second",
                        "content": "Second source snippet.",
                        "raw_content": "",
                    },
                ]
            },
        )

    provider = TavilySearchProvider(api_key="test-key")

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        timeout=30.0,
    ) as client:
        # The provider creates its own AsyncClient, so this test uses
        # a temporary replacement for the HTTP client constructor.
        original_client = httpx.AsyncClient

        class TestAsyncClient:
            def __init__(self, *args, **kwargs):
                self._client = client

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                return await self._client.post(*args, **kwargs)

        httpx.AsyncClient = TestAsyncClient

        try:
            response = await provider.search(
                "AI fact checking",
                max_results=3,
            )
        finally:
            httpx.AsyncClient = original_client

    assert response.query == "AI fact checking"
    assert len(response.results) == 2

    first = response.results[0]

    assert first.title == "AI Fact Checking Research"
    assert first.url == "https://example.com/research"
    assert first.snippet == "A short search-result snippet."
    assert first.content == "Full article content used as evidence."
    assert first.provider == "tavily"


@pytest.mark.asyncio
async def test_tavily_search_falls_back_to_content_when_raw_content_missing() -> None:
    """The normalizer should use Tavily content when raw_content is absent."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Example",
                        "url": "https://example.com",
                        "content": "Useful search result content.",
                    }
                ]
            },
        )

    provider = TavilySearchProvider(api_key="test-key")

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(
        transport=transport,
        timeout=30.0,
    ) as client:
        original_client = httpx.AsyncClient

        class TestAsyncClient:
            def __init__(self, *args, **kwargs):
                self._client = client

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, *args, **kwargs):
                return await self._client.post(*args, **kwargs)

        httpx.AsyncClient = TestAsyncClient

        try:
            response = await provider.search("test query")
        finally:
            httpx.AsyncClient = original_client

    assert len(response.results) == 1
    assert response.results[0].content == "Useful search result content."


@pytest.mark.asyncio
async def test_tavily_search_empty_query_returns_empty_response() -> None:
    """Blank queries should not make an API request."""

    provider = TavilySearchProvider(api_key="test-key")

    response = await provider.search("   ")

    assert response.query == "   "
    assert response.results == []


def test_tavily_provider_rejects_blank_api_key() -> None:
    """A blank API key should fail during provider construction."""

    with pytest.raises(ValueError, match="Tavily API key must not be blank"):
        TavilySearchProvider(api_key="   ")