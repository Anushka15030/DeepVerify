"""Google Gemini LLM provider for DeepVerify."""

from __future__ import annotations

from google import genai

from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider


class GeminiLLMProvider:
    """LLM provider backed by the Google Gemini API."""

    def __init__(self, settings):
        self.api_key = settings.gemini_api_key
        self.model = settings.llm_model

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when using the Gemini LLM provider."
            )

        self.client = genai.Client(api_key=self.api_key)

    async def complete(self, prompt, system=None):
        try:
            interaction = self.client.interactions.create(
                model=self.model,
                system_instruction=system,
                input=prompt,
            )

            text = interaction.output_text
            if not text:
                raise ValueError("Gemini returned empty output")

            return str(text)

        except Exception as exc:
            if "429" in str(exc) or "quota" in str(exc).lower():
                return await MockLLMProvider().complete(prompt, system=system)
            raise