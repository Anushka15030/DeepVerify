"""MinerU-backed document retrieval provider."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.providers.document.base import (
    DocumentSearchResponse,
    DocumentSearchResult,
)


class MinerUDocumentRetrievalProvider:
    """Search parsed MinerU document evidence."""

    provider_name = "mineru"

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> DocumentSearchResponse:
        """Search all parsed MinerU documents for relevant evidence."""

        if not query.strip():
            return DocumentSearchResponse(query=query, results=[])

        elements = self._load_elements()

        query_terms = self._tokenize(query)
        scored: list[tuple[float, DocumentSearchResult]] = []

        for element in elements:
            result = self._element_to_result(element)

            if result is None:
                continue

            score = self._score(result, query_terms)

            if score > 0:
                scored.append((score, result))

        scored.sort(key=lambda item: item[0], reverse=True)

        return DocumentSearchResponse(
            query=query,
            results=[result for _, result in scored[:max_results]],
        )

    def _load_elements(self) -> list[dict[str, Any]]:
        """Load elements from all MinerU content_list_v2 files."""

        if not self.output_dir.exists():
            return []

        elements: list[dict[str, Any]] = []

        for json_path in self.output_dir.rglob("*_content_list_v2.json"):
            try:
                with json_path.open("r", encoding="utf-8") as file:
                    pages = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            if not isinstance(pages, list):
                continue

            document_name = json_path.name.replace(
                "_content_list_v2.json",
                "",
            )

            for page_index, page_elements in enumerate(pages):
                page_number = page_index + 1

                if not isinstance(page_elements, list):
                    continue

                for element in page_elements:
                    if not isinstance(element, dict):
                        continue

                    element_copy = dict(element)
                    element_copy["_page_number"] = page_number
                    element_copy["_document_name"] = document_name
                    element_copy["_json_path"] = str(json_path)

                    elements.append(element_copy)

        return elements

    def _element_to_result(
        self,
        element: dict[str, Any],
    ) -> DocumentSearchResult | None:
        """Convert one MinerU element into our normalized result model."""

        element_type = element.get("type", "")
        content = element.get("content", {})

        if not isinstance(content, dict):
            return None

        # Ignore page numbers, headers, footers and decorative seals.
        if element_type in {
            "page_number",
            "page_header",
            "page_footer",
        }:
            return None

        if element_type == "image" and element.get("sub_type") == "seal":
            return None

        text = self._extract_text(element)

        if not text.strip():
            return None

        page_number = element.get("_page_number")
        document_name = element.get("_document_name")

        if not isinstance(page_number, int) or not document_name:
            return None

        json_path = Path(element["_json_path"])
        document_id = json_path.parent.parent.parent.name

        image_path = self._extract_image_path(element)

        if image_path:
            absolute_image_path = (
                json_path.parent / image_path
            ).resolve()

            image_url = absolute_image_path.as_uri()
        else:
            image_url = None

        bbox = element.get("bbox")

        if not isinstance(bbox, list):
            bbox = None

        return DocumentSearchResult(
            document_id=document_id,
            document_name=document_name,
            page_number=page_number,
            excerpt=text[:4000],
            provider=self.provider_name,
            image_url=image_url,
            bbox=bbox,
            retrieved_at=datetime.now(timezone.utc),
        )

    def _extract_text(self, element: dict[str, Any]) -> str:
        """Extract searchable text from a MinerU element."""

        element_type = element.get("type", "")
        content = element.get("content", {})

        if not isinstance(content, dict):
            return ""

        parts: list[str] = []

        if element_type == "paragraph":
            parts.extend(
                self._extract_nested_text(
                    content.get("paragraph_content", [])
                )
            )

        elif element_type == "title":
            parts.extend(
                self._extract_nested_text(
                    content.get("title_content", [])
                )
            )

        elif element_type == "table":
            captions = self._extract_nested_text(
                content.get("table_caption", [])
            )

            html = content.get("html", "")

            if captions:
                parts.extend(captions)

            if isinstance(html, str):
                parts.append(self._html_to_text(html))

        elif element_type == "image":
            captions = self._extract_nested_text(
                content.get("image_caption", [])
            )

            footnotes = self._extract_nested_text(
                content.get("image_footnote", [])
            )

            image_content = content.get("content", "")

            parts.extend(captions)
            parts.extend(footnotes)

            if isinstance(image_content, str):
                parts.append(image_content)

        else:
            # Generic fallback for other MinerU element types.
            for key, value in content.items():
                if key in {"image_source", "html"}:
                    continue

                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend(self._extract_nested_text(value))

        return " ".join(
            part.strip()
            for part in parts
            if isinstance(part, str) and part.strip()
        )

    def _extract_nested_text(self, value: Any) -> list[str]:
        """Extract text recursively from MinerU nested content."""

        if isinstance(value, str):
            return [value]

        if isinstance(value, list):
            output: list[str] = []

            for item in value:
                output.extend(self._extract_nested_text(item))

            return output

        if isinstance(value, dict):
            output: list[str] = []

            if isinstance(value.get("content"), str):
                output.append(value["content"])

            for key, child in value.items():
                if key == "content":
                    continue

                if isinstance(child, (dict, list)):
                    output.extend(self._extract_nested_text(child))

            return output

        return []

    def _extract_image_path(
        self,
        element: dict[str, Any],
    ) -> str | None:
        """Extract a relative image path from a table or image element."""

        content = element.get("content", {})

        if not isinstance(content, dict):
            return None

        image_source = content.get("image_source")

        if not isinstance(image_source, dict):
            return None

        path = image_source.get("path")

        return path if isinstance(path, str) and path else None

    def _html_to_text(self, html: str) -> str:
        """Convert MinerU table HTML into searchable plain text."""

        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def _tokenize(self, text: str) -> set[str]:
        """Create normalized query tokens."""

        return {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
            if len(token) > 2
        }

    def _score(
        self,
        result: DocumentSearchResult,
        query_terms: set[str],
    ) -> float:
        """Score evidence based on query-term overlap."""

        if not query_terms:
            return 0.0

        text_terms = set(self._tokenize(result.excerpt))

        overlap = query_terms.intersection(text_terms)

        if not overlap:
            return 0.0

        score = len(overlap) / len(query_terms)

        # Give tables a small boost because they contain structured evidence.
        if self._is_table(result.excerpt):
            score += 0.05

        return score

    def _is_table(self, text: str) -> bool:
        """Detect likely table evidence."""

        table_markers = {
            "table",
            "feature",
            "comparison",
            "technical",
            "results",
        }

        tokens = set(self._tokenize(text))

        return bool(tokens.intersection(table_markers))