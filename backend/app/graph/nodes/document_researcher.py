"""Document research graph node."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.models import AgentEvent, Evidence, SourceMetadata
from app.graph.state import DeepVerifyGraphState
from app.providers.document.base import DocumentRetrievalProvider


def make_document_researcher_node(
    document_provider: DocumentRetrievalProvider,
):
    async def document_researcher_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:

        run_id = state.run_id
        plan = state.research_plan

        started = AgentEvent(
            type="search_started",
            run_id=run_id,
            payload={
                "agent": "document_researcher",
                "mode": type(document_provider).__name__,
            },
            timestamp=datetime.now(timezone.utc),
        )

        if not plan:
            completed = AgentEvent(
                type="search_completed",
                run_id=run_id,
                payload={
                    "agent": "document_researcher",
                    "results_count": 0,
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "agent_events": [started, completed],
            }

        evidence: list[Evidence] = []
        total_results = 0

        for subtask in plan.subtasks:
            response = await document_provider.search(
                subtask.query,
                max_results=5,
            )

            total_results += len(response.results)

            for result in response.results:
                if not result.excerpt.strip():
                    continue

                source = SourceMetadata(
                    url=(
                        f"document://{result.document_id}"
                        f"/page/{result.page_number}"
                    ),
                    title=result.document_name,
                    snippet=result.excerpt,
                    provider=result.provider,
                    retrieved_at=result.retrieved_at,
                    document_id=result.document_id,
                    page_number=result.page_number,
                    bbox=result.bbox,
                    image_url=result.image_url,
                )

                evidence.append(
                    Evidence(
                        excerpt=result.excerpt,
                        sources=[source],
                        confidence=0.5,
                    )
                )

        completed = AgentEvent(
            type="search_completed",
            run_id=run_id,
            payload={
                "agent": "document_researcher",
                "mode": type(document_provider).__name__,
                "results_count": total_results,
                "evidence_count": len(evidence),
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "evidence": evidence,
            "agent_events": [started, completed],
        }

    return document_researcher_node