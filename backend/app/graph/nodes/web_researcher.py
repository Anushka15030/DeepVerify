"""Web research graph node using an injected search provider."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.models import AgentEvent, Evidence, SourceMetadata
from app.graph.state import DeepVerifyGraphState
from app.providers.search.base import SearchProvider


def make_web_researcher_node(
    search: SearchProvider,
):
    """Create a web researcher node bound to a search provider."""

    async def web_researcher_node(
        state: DeepVerifyGraphState,
    ) -> dict[str, Any]:
        """Run web searches and convert results into evidence."""

        run_id = state.run_id
        plan = state.research_plan

        # Keep the existing Phase 2 event terminology while the
        # deterministic MockSearchProvider is being used.
        mode = "placeholder"
        provider_name = type(search).__name__

        started = AgentEvent(
            type="search_started",
            run_id=run_id,
            payload={
                "agent": "web_researcher",
                "mode": mode,
                "provider": provider_name,
                "subtask_ids": (
                    [subtask.id for subtask in plan.subtasks]
                    if plan
                    else []
                ),
            },
            timestamp=datetime.now(timezone.utc),
        )

        if not plan:
            completed = AgentEvent(
                type="search_completed",
                run_id=run_id,
                payload={
                    "agent": "web_researcher",
                    "mode": mode,
                    "provider": provider_name,
                    "results_count": 0,
                },
                timestamp=datetime.now(timezone.utc),
            )

            return {
                "agent_events": [started, completed],
                "evidence": [],
            }

        evidence: list[Evidence] = []
        total_results = 0

        for subtask in plan.subtasks:
            response = await search.search(
                subtask.query,
                max_results=5,
            )

            total_results += len(response.results)

            for result in response.results:
                excerpt = result.content.strip() or result.snippet.strip()

                # Search results without usable text cannot become
                # Evidence because Evidence.excerpt is required.
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
            type="search_completed",
            run_id=run_id,
            payload={
                "agent": "web_researcher",
                "mode": mode,
                "provider": provider_name,
                "results_count": total_results,
                "evidence_count": len(evidence),
                "subtask_count": len(plan.subtasks),
            },
            timestamp=datetime.now(timezone.utc),
        )

        return {
            "agent_events": [started, completed],
            "evidence": evidence,
        }

    return web_researcher_node