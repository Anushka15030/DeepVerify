# DeepVerify

DeepVerify is a **multimodal autonomous research & fact-checking engine**: you give it a
question, and it plans, searches, extracts factual claims, verifies them against gathered
evidence, and iterates when grounding is weak — before you get a verdict.

It is built as a **LangGraph workflow** with pluggable LLM and search providers, so the
whole pipeline runs offline against deterministic mocks (no API keys) and is unit-testable
in isolation.

## Features

- **Planner** — decomposes a question into three research subtasks (consensus, empirical,
  counterarguments) via an LLM with strict output validation.
- **Parallel research** — web + document research nodes fan out across subtasks and converge
  on shared evidence.
- **Claim extractor** — pulls factual claims from gathered research with an LLM, falling back
  to a deterministic sentence extractor.
- **Fact checker** — verifies each claim against evidence, returning a strict
  `supported / refuted / unverifiable / inconclusive` verdict plus a grounding score.
- **Revision loop** — weak claims trigger targeted re-research up to a configurable iteration
  cap; grounding scores are averaged across the latest check per claim.
- **Providers** — `mock` (deterministic, offline) and `kie_astra` for LLMs; `mock` and
  `tavily` for search.
- **Event streaming** — every agent emits an SSE-ready `AgentEvent` envelope as the run
  progresses.

## Quickstart

```bash
# offline, no keys — uses mock providers
python -m app.cli "Does coffee increase productivity?"
deepverify "Is London the capital of England?" --json
deepverify "Question" --save --outdir ./reports
```

## Configuration

Settings load from environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `MOCK_MODE` | `true` | Force deterministic mock providers (no API keys) |
| `LLM_PROVIDER` | `mock` | `mock` or `kie_astra` |
| `SEARCH_PROVIDER` | `mock` | `mock` or `tavily` |
| `TAVILY_API_KEY` | — | Required when `SEARCH_PROVIDER=tavily` |
| `GROUNDING_PASS_THRESHOLD` | `0.80` | Minimum grounding score to stop revising |
| `MAX_RESEARCH_ITERATIONS` | `2` | Cap on targeted re-research passes |
| `STORAGE_DIR` | `./storage` | Where artifacts are persisted |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Layout

```
app/
  agents/       # LLM agents + deterministic fallbacks + validation
  core/         # settings, logging, shared Pydantic models
  graph/        # LangGraph state, nodes, workflow wiring
  providers/    # LLM (mock, kie_astra), search (mock, tavily)
  services/     # graph runner, filesystem storage
  cli.py        # command-line entry point
tests/          # pytest suite (offline, deterministic)
```