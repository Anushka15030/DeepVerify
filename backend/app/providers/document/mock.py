"""Deterministic mock document retrieval provider."""

from __future__ import annotations

from app.providers.document.base import (
    DocumentSearchResponse,
    DocumentSearchResult,
)


class MockDocumentRetrievalProvider:
    """Return deterministic document evidence for tests and development."""

    provider_name = "mock"

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> DocumentSearchResponse:

        if not query.strip():
            return DocumentSearchResponse(
                query=query,
                results=[],
            )

        result = DocumentSearchResult(
            document_id="mock-document-001",
            document_name="mock-research-paper.pdf",
            page_number=3,
            excerpt=(
                "This is mock visual document evidence used to test "
                "the DeepVerify document retrieval contract."
            ),
            provider=self.provider_name,
            image_url=None,
            bbox=None,
        )

        return DocumentSearchResponse(
            query=query,
            results=[result][:max_results],
        )