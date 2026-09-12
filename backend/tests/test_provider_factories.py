"""Tests for provider factory functions."""

from __future__ import annotations

import pytest

from app.core.config import clear_settings_cache, create_llm_provider, create_search_provider
from app.providers.llm.kie_astra import KieAstraLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.search.base import SearchProvider
from app.providers.search.mock import MockSearchProvider


def test_factory_returns_mock_llm_by_default() -> None:
    clear_settings_cache()
    provider = create_llm_provider()
    assert isinstance(provider, MockLLMProvider)


def test_factory_returns_mock_search_by_default() -> None:
    clear_settings_cache()
    provider = create_search_provider()
    assert isinstance(provider, MockSearchProvider)
    assert isinstance(provider, SearchProvider)


def test_factory_llm_kie_astra_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "kie_astra")
    monkeypatch.setenv("KIE_API_KEY", "dummy")
    clear_settings_cache()

    provider = create_llm_provider()
    assert isinstance(provider, KieAstraLLMProvider)


def test_factory_search_mock_when_mock_mode_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    clear_settings_cache()

    provider = create_search_provider()
    assert isinstance(provider, MockSearchProvider)
