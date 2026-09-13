"""Decision logic for triggering additional research iterations."""

from __future__ import annotations

from app.core.config import Settings
from app.core.models import ClaimCheck


class RevisionDecider:
    """Decide whether the current research needs another iteration."""

    def __init__(self, settings: Settings) -> None:
        self.threshold = settings.grounding_pass_threshold
        self.max_iterations = settings.max_research_iterations

    def should_revise(
        self,
        grounding_score: float | None,
        revision_count: int,
    ) -> bool:
        if grounding_score is None:
            return True

        if grounding_score >= self.threshold:
            return False

        return revision_count < self.max_iterations

    def build_queries(
        self,
        claim_checks: list[ClaimCheck],
    ) -> list[str]:
        """Build one targeted query per unique weak claim using the latest check."""

        # Keep only the latest check for each claim.
        latest_checks: dict[str, ClaimCheck] = {}

        for check in claim_checks:
            claim = check.claim.strip()

            if not claim:
                continue

            latest_checks[claim] = check

        # Create targeted searches only for weak claims.
        queries: list[str] = []

        for claim, check in latest_checks.items():
            if check.grounding_score >= self.threshold:
                continue

            queries.append(
                f"Verify this claim with reliable sources: {claim}"
            )

        return queries