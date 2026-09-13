"""KIE GPT-6 Astra LLM provider."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.core.config import Settings


class KieAstraLLMProvider:
    """KIE GPT-6 Astra client implementing the LLMProvider interface."""

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.kie_api_key
        self.base_url = settings.kie_base_url.rstrip("/")
        self.model = settings.llm_model

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        if not self.api_key:
            raise ValueError(
                "KIE_API_KEY is not configured. "
                "Set KIE_API_KEY or enable MOCK_MODE."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        text = prompt

        if system:
            text = f"{system}\n\nUser request:\n{prompt}"

        payload = {
            "model": self.model,
            "stream": False,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text,
                        }
                    ],
                }
            ],
            "reasoning": {
                "effort": "low",
            },
        }

        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
        ) as client:
            response = await client.post(
                "/codex/v1/responses",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        for item in data.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    text = content.get("text")
                    if text:
                        return str(text)

        raise ValueError(
            "KIE Astra returned no output text."
        )