"""Research API endpoints for DeepVerify."""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.models import AgentEvent
from app.services.graph_runner import run_research


router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    """Request body for starting a research run."""

    question: str


class ResearchStartResponse(BaseModel):
    """Response returned when a research run starts."""

    run_id: str
    status: str


# In-memory storage is sufficient for the hackathon prototype.
_events: dict[str, list[AgentEvent]] = defaultdict(list)
_results: dict[str, object] = {}
_tasks: dict[str, asyncio.Task] = {}


async def _run_research_background(
    run_id: str,
    question: str,
) -> None:
    """Run research in the background and store the final result."""

    try:
        state = await run_research(
            question,
            run_id=run_id,
        )

        _results[run_id] = state

        # run_research already adds run_completed.
        _events[run_id].extend(state.agent_events)

    except Exception as exc:
        _events[run_id].append(
            AgentEvent(
                type="error",
                run_id=run_id,
                payload={
                    "message": str(exc),
                },
            )
        )


@router.post("", response_model=ResearchStartResponse)
async def start_research(
    request: ResearchRequest,
) -> ResearchStartResponse:
    """Start a research run in the background."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question must not be blank.",
        )

    run_id = str(uuid.uuid4())

    _events[run_id] = []

    task = asyncio.create_task(
        _run_research_background(
            run_id=run_id,
            question=question,
        )
    )

    _tasks[run_id] = task

    return ResearchStartResponse(
        run_id=run_id,
        status="started",
    )


@router.get("/{run_id}")
async def get_research(run_id: str):
    """Return the final research state."""

    if run_id not in _tasks:
        raise HTTPException(
            status_code=404,
            detail="Research run not found.",
        )

    if run_id not in _results:
        return {
            "run_id": run_id,
            "status": "running",
        }

    state = _results[run_id]

    return state.model_dump(mode="json")


@router.get("/{run_id}/events")
async def research_events(run_id: str):
    """Stream research events using Server-Sent Events."""

    if run_id not in _tasks:
        raise HTTPException(
            status_code=404,
            detail="Research run not found.",
        )

    async def event_generator():
        sent = 0

        while True:
            current_events = _events.get(run_id, [])

            while sent < len(current_events):
                event = current_events[sent]
                sent += 1

                yield (
                    "event: agent_event\n"
                    f"data: {event.model_dump_json()}\n\n"
                )

            if run_id in _results:
                break

            task = _tasks.get(run_id)

            if task is not None and task.done():
                break

            await asyncio.sleep(0.25)

        # Send a clean SSE termination event.
        yield "event: stream_end\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )