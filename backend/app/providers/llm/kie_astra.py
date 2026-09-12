"""Kie Astra LLM provider stub (config-driven, not wired into workflow)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.core.config import Settings


class KieAstraLLMProvider:
    """Stub Kie Astra LLM client. Requires KIE_API_KEY when not in stub mode."""

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.kie_api_key
        self.base_url = settings.kie_base_url.rstrip("/")
        self.model = settings.llm_model

    async def complete(self, prompt: str, system: str | None = None) -> str:
        if not self.api_key:
            raise ValueError(
                "KIE_API_KEY is not configured. Set KIE_API_KEY or enable MOCK_MODE."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": prompt},
            ],
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            return f"[kie-astra stub] No choices returned for model={self.model}."

        message = choices[0].get("message") or {}
        content = message.get("content")
        if content:
            return str(content)

        return f"[kie-astra stub] Empty response for model={self.model}."
