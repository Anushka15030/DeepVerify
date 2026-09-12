"""Tests for application settings and provider factories."""

from __future__ import annotations

import pytest

from app.core.config import (
    Settings,
    clear_settings_cache,
    create_llm_provider,
    create_search_provider,
    get_settings,
)
from app.providers.llm.kie_astra import KieAstraLLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.search.mock import MockSearchProvider


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.mock_mode is True
    assert settings.llm_provider == "mock"
    assert settings.llm_model == "mock-gpt"
    assert settings.kie_api_key == ""
    assert settings.search_provider == "mock"
    assert settings.document_retrieval_provider == "mock"
    assert settings.max_research_iterations == 3
    assert settings.grounding_pass_threshold == 0.7
    assert settings.storage_dir == "./storage"


def test_get_settings_is_singleton() -> None:
    clear_settings_cache()
    first = get_settings()
    second = get_settings()
    assert first is second


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "kie_astra")
    monkeypatch.setenv("LLM_MODEL", "astra-large")
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("MAX_RESEARCH_ITERATIONS", "5")
    monkeypatch.setenv("GROUNDING_PASS_THRESHOLD", "0.85")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/deepverify")
    clear_settings_cache()

    settings = get_settings()
    assert settings.app_env == "testing"
    assert settings.log_level == "DEBUG"
    assert settings.mock_mode is False
    assert settings.llm_provider == "kie_astra"
    assert settings.llm_model == "astra-large"
    assert settings.max_research_iterations == 5
    assert settings.grounding_pass_threshold == 0.85
    assert settings.storage_dir == "/tmp/deepverify"


def test_mock_mode_forces_mock_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("LLM_PROVIDER", "kie_astra")
    clear_settings_cache()

    provider = create_llm_provider()
    assert isinstance(provider, MockLLMProvider)


def test_mock_mode_forces_mock_search_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("SEARCH_PROVIDER", "unknown")
    clear_settings_cache()

    provider = create_search_provider()
    assert isinstance(provider, MockSearchProvider)


def test_create_llm_provider_respects_provider_when_not_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "kie_astra")
    monkeypatch.setenv("KIE_API_KEY", "test-key")
    clear_settings_cache()

    provider = create_llm_provider()
    assert isinstance(provider, KieAstraLLMProvider)


def test_create_search_provider_unknown_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "false")
    monkeypatch.setenv("SEARCH_PROVIDER", "serpapi")
    clear_settings_cache()

    with pytest.raises(ValueError, match="Unsupported search provider"):
        create_search_provider()
