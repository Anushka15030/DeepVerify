"""Command-line interface for running DeepVerify research workflows.

Usage:
    deepverify "Is London the capital of England?"
    deepverify "Does coffee increase productivity?" --json
    deepverify "Question" --save --outdir ./reports
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.config import create_llm_provider, create_search_provider, get_settings
from app.core.models import AgentEvent
from app.graph.state import DeepVerifyState
from app.services.graph_runner import run_research
from app.services.storage import FileStorage


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deepverify",
        description="Run DeepVerify's autonomous research and fact-checking engine on a question.",
    )
    parser.add_argument(
        "question",
        nargs="+",
        help="The research question to investigate.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full run result as JSON instead of a human-readable report.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Persist the run result to the storage directory as JSON.",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help="Override the storage directory (default: STORAGE_DIR setting).",
    )
    return parser


def _question_from_args(args: argparse.Namespace) -> str:
    return " ".join(args.question)


def _format_report(state: DeepVerifyState) -> str:
    """Render a compact human-readable report from a finished run."""
    lines: list[str] = []

    plan = state.research_plan
    if plan is not None:
        lines.append(f"topic: {plan.topic}")
        lines.append(
            f"subtasks: {len(plan.subtasks)} "
            f"({', '.join(s.id for s in plan.subtasks)})"
        )

    lines.append(f"claims extracted: {len(state.claims)}")
    checks = state.claim_checks
    if checks:
        lines.append(f"claims checked: {len(checks)}")
        verdict_counts: dict[str, int] = {}
        for check in checks:
            verdict_counts[check.verdict] = (
                verdict_counts.get(check.verdict, 0) + 1
            )
        summary = ", ".join(
            f"{verdict}={count}" for verdict, count in sorted(verdict_counts.items())
        )
        lines.append(f"  verdicts: {summary}")

    score = state.grounding_score
    lines.append(
        f"grounding score: {score:.3f}" if score is not None else "grounding score: n/a"
    )
    lines.append(f"revision count: {state.revision_count}")

    errors = state.errors
    if errors:
        lines.append(f"errors: {len(errors)}")
        for error in errors[:5]:
            lines.append(f"  - {error}")

    def _count(etype: str) -> int:
        return sum(1 for e in state.agent_events if e.type == etype)

    events: list[AgentEvent] = state.agent_events
    if events:
        lines.append(
            f"events: {len(events)} "
            f"(plan={_count('plan_created')}, "
            f"search={_count('search_completed')}, "
            f"check={_count('claim_checked')}, "
            f"revision={_count('revision_requested')})"
        )

    return "\n".join(lines)


async def _run(
    question: str,
    *,
    run_id: str | None = None,
) -> DeepVerifyState:
    settings = get_settings()
    return await run_research(
        question,
        run_id=run_id,
        llm=create_llm_provider(settings),
        search=create_search_provider(settings),
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    question = _question_from_args(args)

    try:
        state = asyncio.run(_run(question))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"error: research run failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(state.model_dump_json(indent=2))
    else:
        print(_format_report(state))

    if args.save:
        storage = FileStorage(base_dir=args.outdir) if args.outdir else FileStorage()
        path = storage.write_json(f"runs/{state.run_id}.json", state.model_dump(mode="json"))
        print(f"saved: {path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())