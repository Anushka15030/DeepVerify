"""Tests for mock LLM provider."""

from __future__ import annotations

import pytest

from app.providers.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_llm_is_deterministic() -> None:
    provider = MockLLMProvider(model="mock-gpt")
    first = await provider.complete("Explain transformers.", system="You are helpful.")
    second = await provider.complete("Explain transformers.", system="You are helpful.")
    assert first == second


@pytest.mark.asyncio
async def test_mock_llm_differs_for_different_prompts() -> None:
    provider = MockLLMProvider()
    response_a = await provider.complete("prompt A")
    response_b = await provider.complete("prompt B")
    assert response_a != response_b


@pytest.mark.asyncio
async def test_mock_llm_no_api_key_required() -> None:
    provider = MockLLMProvider()
    result = await provider.complete("hello")
    assert "mock-llm" in result
