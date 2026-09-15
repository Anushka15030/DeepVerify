"""Fact-checking logic for DeepVerify."""

from __future__ import annotations

import re

from app.core.models import ClaimCheck, Evidence


_STOP_WORDS = {
    "the",
    "and",
    "was",
    "were",
    "is",
    "are",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "by",
    "from",
    "this",
    "that",
    "it",
}


def _tokenize(text: str) -> set[str]:
    """Convert text into normalized meaningful tokens."""

    return {
        token
        for token in re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        if len(token) >= 3 and token not in _STOP_WORDS
    }


class FactChecker:
    """Evaluate claims against collected evidence."""

    def check_claim(
        self,
        claim: str,
        evidence: list[Evidence],
    ) -> ClaimCheck:
        """Perform deterministic fallback verification."""

        if not claim.strip():
            raise ValueError("claim must not be blank")

        usable_evidence = [
            item
            for item in evidence
            if item.excerpt.strip()
        ]

        if not usable_evidence:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                verification_method="deterministic_fallback",
                explanation=(
                    "No usable evidence was available to verify this claim."
                ),
            )

        claim_tokens = _tokenize(claim)

        scored_evidence: list[tuple[int, Evidence]] = []

        for item in usable_evidence:
            evidence_tokens = _tokenize(item.excerpt)

            overlap = len(claim_tokens & evidence_tokens)

            if overlap > 0:
                scored_evidence.append((overlap, item))

        scored_evidence.sort(
            key=lambda pair: pair[0],
            reverse=True,
        )

        if scored_evidence:
            relevant_evidence = [
                item
                for _, item in scored_evidence
            ]

            explanation = (
                "Relevant evidence was found, but the deterministic "
                "fallback cannot reliably determine whether the claim "
                "is supported or refuted."
            )
        else:
            relevant_evidence = usable_evidence

            explanation = (
                "Evidence was available, but no clearly relevant "
                "evidence match was identified. The deterministic "
                "fallback cannot reliably determine whether the claim "
                "is supported or refuted."
            )

        average_confidence = sum(
            item.confidence
            for item in relevant_evidence
        ) / len(relevant_evidence)

        return ClaimCheck(
            claim=claim,
            verdict="inconclusive",
            evidence=relevant_evidence,
            grounding_score=average_confidence,
            verification_method="deterministic_fallback",
            explanation=explanation,
        )