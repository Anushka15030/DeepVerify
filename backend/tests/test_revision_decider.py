from app.agents.revision_decider import RevisionDecider
from app.core.config import Settings
from app.core.models import ClaimCheck


def make_decider() -> RevisionDecider:
    settings = Settings(
        grounding_pass_threshold=0.80,
        max_research_iterations=2,
    )
    return RevisionDecider(settings)


def test_does_not_revise_when_score_passes() -> None:
    decider = make_decider()

    assert decider.should_revise(
        grounding_score=0.85,
        revision_count=0,
    ) is False


def test_revises_when_score_is_below_threshold() -> None:
    decider = make_decider()

    assert decider.should_revise(
        grounding_score=0.60,
        revision_count=0,
    ) is True


def test_does_not_exceed_max_iterations() -> None:
    decider = make_decider()

    assert decider.should_revise(
        grounding_score=0.60,
        revision_count=2,
    ) is False


def test_none_score_triggers_revision() -> None:
    decider = make_decider()

    assert decider.should_revise(
        grounding_score=None,
        revision_count=0,
    ) is True


def test_builds_queries_for_weak_claims() -> None:
    decider = make_decider()

    checks = [
        ClaimCheck(
            claim="The rainfall increased by 40 percent.",
            verdict="inconclusive",
            grounding_score=0.40,
            explanation="Insufficient evidence.",
        ),
        ClaimCheck(
            claim="The system uses PostgreSQL.",
            verdict="supported",
            grounding_score=0.95,
            explanation="Directly supported.",
        ),
    ]

    queries = decider.build_queries(checks)

    assert len(queries) == 1
    assert "rainfall increased by 40 percent" in queries[0]