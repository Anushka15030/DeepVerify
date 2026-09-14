"""Claim extraction logic for DeepVerify."""

from __future__ import annotations

import re


class ClaimExtractor:
    """Extract factual claims from generated research text."""

    def extract(self, text: str) -> list[str]:
        """Extract candidate factual claims from text.

        This deterministic implementation provides a baseline before
        LLM-based claim extraction is introduced.
        """
        if not text.strip():
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        claims: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            # Ignore questions.
            if sentence.endswith("?"):
                continue

            # Ignore very short fragments.
            if len(sentence.split()) < 5:
                continue

            claims.append(sentence)

            if len(claims) >= 8:
                break

        return claims