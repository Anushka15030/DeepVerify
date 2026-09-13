"""LangGraph node for targeted research during revision iterations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.models import AgentEvent, Evidence, SourceMetadata
from app.graph.state import DeepVerifyGraphState
from app.providers.search.base import SearchProvider


def make_revision_researcher_node(search: SearchProvider):
    """Create a revision researcher node using the configured search provider."""

    async def revision_researcher_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:
        run_id = state.run_id
        queries = state.revision_queries

        provider_name = type(search).__name__

        started = AgentEvent(
            type="revision_search_started",
            run_id=run_id,
            payload={
                "agent": "revision_researcher",
                "provider": provider_name,
                "queries_count": len(queries),
            },
            timestamp=datetime.now(timezone.utc),
        )

        if not queries:
            completed = AgentEvent(
                type="revision_search_completed",
                run_id=run_id,
                payload={
                    "agent": "revision_researcher",
                    "provider": provider_name,
                    "queries_count": 0,
                    "results_count": 0,
                    "evidence_count": 0,
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "evidence": [],
                "agent_events": [started, completed],
            }

        evidence: list[Evidence] = []
        total_results = 0

        for query in queries:
            response = await search.search(
                query,
                max_results=5,
            )

            total_results += len(response.results)

            for result in response.results:
                excerpt = (
                    result.content.strip()
                    or result.snippet.strip()
                )

                if not excerpt:
                    continue

                source = SourceMetadata(
                    url=result.url,
                    title=result.title,
                    snippet=result.snippet,
                    retrieved_at=result.retrieved_at,
                    provider=result.provider,
                )

                evidence.append(
                    Evidence(
                        excerpt=excerpt,
                        sources=[source],
                        confidence=0.5,
                    )
                )

        completed = AgentEvent(
            type="revision_search_completed",
            run_id=run_id,
            payload={
                "agent": "revision_researcher",
                "provider": provider_name,
                "queries_count": len(queries),
                "results_count": total_results,
                "evidence_count": len(evidence),
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "evidence": evidence,
            "agent_events": [started, completed],
        }

    return revision_researcher_node