# DeepVerify

> Multimodal autonomous research & fact-checking engine.

DeepVerify turns a plain question into a verifiable research run: it plans a structured
investigation, searches the web, extracts factual claims, checks them against gathered
evidence, and re-researches anything still weakly grounded — then reports its verdict.

The project lives in the [`backend/`](backend/) directory. See
[`backend/README.md`](backend/README.md) for architecture, quickstart, and configuration.

## Highlights

- **LangGraph workflow** with parallel research, claim extraction, fact-checking, and a
  revision loop.
- **Pluggable providers** — LLM (`mock`, `kie_astra`) and search (`mock`, `tavily`).
- **Fully offline in mock mode** — deterministic, no API keys, unit-testable.
- **Event streaming** — every agent emits an SSE-ready event envelope.
- **Strict verdicts** — `supported / refuted / unverifiable / inconclusive` with grounding
  scores.

## Quickstart

```bash
cd backend
pip install -e ".[dev]"
deepverify "Does coffee increase productivity?"
deepverify "Is London the capital of England?" --json
```

## License

MIT