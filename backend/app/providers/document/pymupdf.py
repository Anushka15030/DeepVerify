"""PyMuPDF-backed PDF document retrieval provider."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf

from app.providers.document.base import (
    DocumentSearchResponse,
    DocumentSearchResult,
)


class PyMuPDFDocumentRetrievalProvider:
    """Search PDF documents directly using PyMuPDF."""

    provider_name = "pymupdf"

    def __init__(self, input_dir: str | Path):
        self.input_dir = Path(input_dir)

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> DocumentSearchResponse:
        if not query.strip():
            return DocumentSearchResponse(query=query, results=[])

        query_terms = self._tokenize(query)

        if not query_terms:
            return DocumentSearchResponse(query=query, results=[])

        scored: list[tuple[float, DocumentSearchResult]] = []

        for pdf_path in self.input_dir.glob("*.pdf"):
            try:
                document = pymupdf.open(pdf_path)
            except Exception:
                continue

            try:
                for page_index, page in enumerate(document):
                    text = page.get_text("text").strip()

                    if not text:
                        continue

                    score = self._score(text, query_terms)

                    if score < 0.34:
                        continue

                    # Get the bounding rectangle of the matching text.
                    bbox = self._matching_bbox(page, query_terms)

                    scored.append(
                        (
                            score,
                            DocumentSearchResult(
                                document_id=pdf_path.stem,
                                document_name=pdf_path.stem,
                                page_number=page_index + 1,
                                excerpt=text[:4000],
                                provider=self.provider_name,
                                image_url=None,
                                bbox=bbox,
                                retrieved_at=datetime.now(timezone.utc),
                            ),
                        )
                    )
            finally:
                document.close()

        scored.sort(key=lambda item: item[0], reverse=True)

        return DocumentSearchResponse(
            query=query,
            results=[result for _, result in scored[:max_results]],
        )

    def _tokenize(self, text: str) -> set[str]:
        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "are",
            "what",
            "how",
            "why",
            "can",
            "does",
            "into",
            "about",
            "their",
            "there",
            "these",
            "those",
            "major",
            "systems",
            "system",
            "research",
            "evidence",
            "data",
            "study",
            "studies",
            "analysis",
            "information",
            "challenges",
            "challenge",
            "limitations",
            "limitation",
            "risks",
            "risk",
            "concerns",
            "concern",
            "issues",
            "issue",
        }

        return {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if len(token) > 2 and token not in stop_words
        }

    def _score(
        self,
        text: str,
        query_terms: set[str],
    ) -> float:
        text_terms = self._tokenize(text)
        overlap = query_terms.intersection(text_terms)

        if len(overlap) < 2:
            return 0.0

        return min(len(overlap) / len(query_terms), 1.0)

    def _matching_bbox(
        self,
        page: Any,
        query_terms: set[str],
    ) -> list[float] | None:
        """Return a bbox covering the first matching text block."""

        blocks = page.get_text("blocks")

        for block in blocks:
            if len(block) < 5:
                continue

            block_text = str(block[4])
            block_terms = self._tokenize(block_text)

            if len(query_terms.intersection(block_terms)) >= 2:
                return [
                    float(block[0]),
                    float(block[1]),
                    float(block[2]),
                    float(block[3]),
                ]

        return None