"""LLM provider protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for async LLM completion providers."""

    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate a completion for the given prompt."""
        ...
