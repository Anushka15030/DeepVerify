"""Document retrieval provider interfaces and normalized result models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class DocumentSearchResult(BaseModel):
    """A normalized result returned by a document retrieval provider."""

    document_id: str
    document_name: str
    page_number: int = Field(ge=1)

    excerpt: str
    provider: str

    # Optional visual evidence information.
    image_url: str | None = None
    bbox: list[float] | None = None

    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DocumentSearchResponse(BaseModel):
    """Normalized response from a document retrieval provider."""

    query: str
    results: list[DocumentSearchResult] = Field(default_factory=list)


@runtime_checkable
class DocumentRetrievalProvider(Protocol):
    """Provider interface for searching indexed documents."""

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
    ) -> DocumentSearchResponse:
        ...