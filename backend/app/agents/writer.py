"""LLM-powered research dossier writer."""

from __future__ import annotations

import json
from typing import Any

from app.core.models import ClaimCheck, Evidence
from app.providers.llm.base import LLMProvider


MAX_CLAIMS = 8
MAX_EVIDENCE_PER_CLAIM = 3
MAX_EXCERPT_CHARS = 900


def _compact_evidence(
    claim_checks: list[ClaimCheck],
) -> tuple[str, list[dict[str, Any]]]:
    """Build compact evidence context and a citation registry."""

    citation_registry: list[dict[str, Any]] = []
    blocks: list[str] = []

    citation_number = 1

    for check in claim_checks[:MAX_CLAIMS]:
        blocks.append(f"CLAIM: {check.claim}")
        blocks.append(f"VERDICT: {check.verdict}")
        blocks.append(f"SCORE: {check.grounding_score:.2f}")
        blocks.append(f"EXPLANATION: {check.explanation[:300]}")

        for evidence in check.evidence[:MAX_EVIDENCE_PER_CLAIM]:
            source = evidence.sources[0] if evidence.sources else None

            if source is None:
                continue

            citation_registry.append(
                {
                    "number": citation_number,
                    "title": source.title,
                    "url": source.url,
                    "provider": source.provider,
                    "document_id": source.document_id,
                    "page_number": source.page_number,
                    "bbox": source.bbox,
                    "image_url": source.image_url,
                    "snippet": source.snippet[:300],
                }
            )

            blocks.append(
                f"EVIDENCE [{citation_number}]: "
                f"{evidence.excerpt[:MAX_EXCERPT_CHARS]}"
            )

            citation_number += 1

        blocks.append("")

    return "\n".join(blocks), citation_registry


def _format_citations(citations: list[dict[str, Any]]) -> str:
    """Format citation registry for the final dossier."""

    lines: list[str] = []

    for citation in citations:
        number = citation["number"]
        title = citation["title"]
        url = citation["url"]
        provider = citation["provider"]

        location = ""

        if citation.get("page_number") is not None:
            location = f", p. {citation['page_number']}"

        lines.append(
            f"[{number}] {title}{location} — {provider} — {url}"
        )

    return "\n".join(lines)


async def write_dossier(
    llm: LLMProvider,
    question: str,
    claim_checks: list[ClaimCheck],
) -> str:
    """Generate a concise, citation-grounded research dossier."""

    evidence_context, citations = _compact_evidence(claim_checks)

    citation_text = _format_citations(citations)

    system = """You are the final research dossier writer.

Write a concise, evidence-grounded research report.

Rules:
- Use only information supported by the supplied evidence.
- Never invent statistics, studies, dates, organizations, or conclusions.
- Do not strengthen a claim beyond its evidence.
- Cite factual statements using [N] notation.
- Use the supplied citation numbers exactly.
- If evidence is inconclusive, say so.
- Clearly distinguish established findings from limitations or counterarguments.
- Do not include a references section yourself.
- Return Markdown only.
"""

    prompt = f"""Research question:
{question}

Verified claim evidence:
{evidence_context}

Write a research dossier with this structure:

# Research Dossier

## Executive Summary

Give a concise answer to the research question.

## Key Findings

Present the strongest supported findings with inline citations.

## Evidence and Analysis

Explain the important evidence and what it establishes.

## Limitations and Counterarguments

Include claims that were refuted, inconclusive, unverifiable, or limited by the evidence.

## Conclusion

Give a balanced conclusion supported by the evidence.

Citation registry:
{citation_text}
"""

    raw = await llm.complete(prompt, system=system)

    # Protect the pipeline if the model accidentally returns JSON.
    text = raw.strip()

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()

        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict) and isinstance(parsed.get("draft"), str):
            text = parsed["draft"].strip()
    except (json.JSONDecodeError, TypeError):
        pass

    if not text:
        raise ValueError("Writer returned an empty dossier.")

    references = "\n\n## References\n\n" + citation_text

    return text + references