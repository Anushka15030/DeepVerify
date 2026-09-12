"""Fact-checking logic for DeepVerify."""

from __future__ import annotations

from app.core.models import ClaimCheck, Evidence


class FactChecker:
    """Evaluate claims against collected evidence."""

    def check_claim(
        self,
        claim: str,
        evidence: list[Evidence],
    ) -> ClaimCheck:
        """Check a claim against available evidence.

        This first implementation is deterministic and serves as the
        baseline before LLM-based adversarial verification is added.
        """

        if not claim.strip():
            raise ValueError("claim must not be blank")

        if not evidence:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                explanation="No evidence was available to verify this claim.",
            )

        relevant_evidence = [
            item for item in evidence
            if item.excerpt.strip()
        ]

        if not relevant_evidence:
            return ClaimCheck(
                claim=claim,
                verdict="unverifiable",
                evidence=[],
                grounding_score=0.0,
                explanation="Available evidence contained no usable excerpts.",
            )

        average_confidence = sum(
            item.confidence for item in relevant_evidence
        ) / len(relevant_evidence)

        return ClaimCheck(
            claim=claim,
            verdict="inconclusive",
            evidence=relevant_evidence,
            grounding_score=average_confidence,
            explanation=(
                "Evidence is available, but semantic claim verification "
                "has not yet been performed."
            ),
        )