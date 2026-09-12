"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.core.config import clear_settings_cache


_DEFAULT_ENV = {
    "APP_ENV": "development",
    "LOG_LEVEL": "INFO",
    "MOCK_MODE": "true",
    "LLM_PROVIDER": "mock",
    "LLM_MODEL": "mock-gpt",
    "KIE_API_KEY": "",
    "KIE_BASE_URL": "https://api.kie.example/v1",
    "SEARCH_PROVIDER": "mock",
    "DOCUMENT_RETRIEVAL_PROVIDER": "mock",
    "MAX_RESEARCH_ITERATIONS": "3",
    "GROUNDING_PASS_THRESHOLD": "0.7",
    "STORAGE_DIR": "./storage",
}


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure each test starts with a fresh, isolated settings cache."""
    clear_settings_cache()
    for key, value in _DEFAULT_ENV.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def tmp_storage_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide an isolated storage directory for filesystem tests."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    monkeypatch.setenv("STORAGE_DIR", str(storage_dir))
    clear_settings_cache()
    return storage_dir
