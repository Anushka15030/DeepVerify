"""Tests for the deepverify command-line interface."""

from __future__ import annotations

import json

from app.cli import _build_parser, _format_report, main


def test_parser_parses_question_and_flags() -> None:
    parser = _build_parser()
    args = parser.parse_args(["Is", "London", "capital?", "--json", "--save"])
    assert args.question == ["Is", "London", "capital?"]
    assert args.json is True
    assert args.save is True


def test_parser_defaults() -> None:
    args = _build_parser().parse_args(["a", "b"])
    assert args.json is False
    assert args.save is False
    assert args.outdir is None


def test_main_runs_question_and_reports(monkeypatch) -> None:
    """Runs end-to-end in mock mode (offline) and prints a readable report."""
    import io

    captured = io.StringIO()

    class _P:
        def write(self, s):
            captured.write(s)
            return len(s)

    monkeypatch.setattr("sys.stdout", _P())
    monkeypatch.setattr("sys.stderr", _P())

    code = main(["Does", "coffee", "increase", "productivity?"])
    assert code == 0
    text = captured.getvalue()
    assert "topic:" in text
    assert "subtasks:" in text
    assert "grounding score:" in text
    assert "verdicts:" in text


def test_main_json_output(monkeypatch) -> None:
    import io

    captured = io.StringIO()

    class _P:
        def write(self, s):
            captured.write(s)
            return len(s)

    monkeypatch.setattr("sys.stdout", _P())
    monkeypatch.setattr("sys.stderr", _P())

    code = main(["London", "capital?", "--json"])
    assert code == 0
    data = json.loads(captured.getvalue())
    assert data["original_question"] == "London capital?"
    assert data["research_plan"] is not None
    assert len(data["research_plan"]["subtasks"]) == 3


def test_main_save_writes_storage(monkeypatch, tmp_path) -> None:
    import io

    captured = io.StringIO()

    class _P:
        def write(self, s):
            captured.write(s)
            return len(s)

    monkeypatch.setattr("sys.stdout", _P())
    monkeypatch.setattr("sys.stderr", _P())

    outdir = tmp_path / "reports"
    code = main(["save", "test", "--save", "--outdir", str(outdir)])
    assert code == 0
    saved_file = str(outdir / "runs_*.json")
    import glob

    assert glob.glob(saved_file), "expected a saved run artifact"


def test_format_report_with_errors() -> None:
    from app.core.models import AgentEvent
    from app.graph.state import DeepVerifyState

    state = DeepVerifyState(
        run_id="r1",
        original_question="q",
        errors=["boom"],
        agent_events=[
            AgentEvent(type="error", run_id="r1", payload={"message": "boom"})
        ],
    )
    report = _format_report(state)
    assert "errors: 1" in report
    assert "- boom" in report