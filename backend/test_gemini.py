import asyncio

from app.core.config import get_settings
from app.providers.llm.gemini import GeminiLLMProvider


async def main():
    settings = get_settings()

    provider = GeminiLLMProvider(settings)

    response = await provider.complete(
        prompt="Explain what an AI fact-checking system does in 3 short sentences.",
        system=(
            "You are a concise technical assistant. "
            "Answer accurately and do not invent facts."
        ),
    )

    print("\n--- GEMINI RESPONSE ---")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())