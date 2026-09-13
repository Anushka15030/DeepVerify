"""Application settings and provider factories."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.providers.document.base import DocumentRetrievalProvider

if TYPE_CHECKING:
    from app.providers.llm.base import LLMProvider
    from app.providers.search.base import SearchProvider


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",

    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    mock_mode: bool = Field(default=True, alias="MOCK_MODE")

    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="mock-gpt", alias="LLM_MODEL")

    kie_api_key: str = Field(default="", alias="KIE_API_KEY")
  
    kie_base_url: str = Field(
    default="https://api.kie.ai",
    alias="KIE_BASE_URL",
    )

    search_provider: str = Field(
        default="mock",
        alias="SEARCH_PROVIDER",
    )
    tavily_api_key: str = Field(
        default="",
        alias="TAVILY_API_KEY",
    )

    document_retrieval_provider: str = Field(
        default="mock",
        alias="DOCUMENT_RETRIEVAL_PROVIDER",
    )

    grounding_pass_threshold: float = Field(
        default=0.80,
        alias="GROUNDING_PASS_THRESHOLD",
    )

    max_research_iterations: int = Field(
        default=2,
        alias="MAX_RESEARCH_ITERATIONS",
    )

    storage_dir: str = Field(
        default="./storage",
        alias="STORAGE_DIR",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache (primarily for tests)."""

    get_settings.cache_clear()


def create_llm_provider(
    settings: Settings | None = None,
) -> LLMProvider:
    """Create an LLM provider based on settings and mock mode."""

    from app.providers.llm.kie_astra import KieAstraLLMProvider
    from app.providers.llm.mock import MockLLMProvider

    cfg = settings or get_settings()

    if cfg.mock_mode:
        return MockLLMProvider(model=cfg.llm_model)

    provider_name = cfg.llm_provider.lower()

    if provider_name == "mock":
        return MockLLMProvider(model=cfg.llm_model)

    if provider_name == "kie_astra":
        return KieAstraLLMProvider(settings=cfg)

    raise ValueError(
        f"Unsupported LLM provider: {cfg.llm_provider}"
    )


def create_search_provider(
    settings: Settings | None = None,
) -> SearchProvider:
    """Create a search provider based on settings and mock mode."""

    from app.providers.search.mock import MockSearchProvider
    from app.providers.search.tavily import TavilySearchProvider

    cfg = settings or get_settings()

    if cfg.mock_mode:
        return MockSearchProvider()

    provider_name = cfg.search_provider.lower()

    if provider_name == "mock":
        return MockSearchProvider()

    if provider_name == "tavily":
        if not cfg.tavily_api_key.strip():
            raise ValueError(
                "TAVILY_API_KEY must be set when using the Tavily search provider"
            )

        return TavilySearchProvider(
            api_key=cfg.tavily_api_key,
        )

    raise ValueError(
        f"Unsupported search provider: {cfg.search_provider}"
    )


def create_document_retrieval_provider(
    settings: Settings | None = None,
) -> DocumentRetrievalProvider:
    from app.providers.document.mock import MockDocumentRetrievalProvider

    cfg = settings or get_settings()

    provider_name = cfg.document_retrieval_provider.lower()

    if cfg.mock_mode:
        return MockDocumentRetrievalProvider()

    if provider_name == "mock":
        return MockDocumentRetrievalProvider()

    raise ValueError(
        f"Unsupported document retrieval provider: "
        f"{cfg.document_retrieval_provider}"
    )