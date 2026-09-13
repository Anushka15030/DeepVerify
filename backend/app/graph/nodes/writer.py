"""Graph node for generating the final research dossier."""

from __future__ import annotations

from app.agents.writer import write_dossier
from app.graph.state import DeepVerifyGraphState
from app.providers.llm.base import LLMProvider


def make_writer_node(llm: LLMProvider):
    """Create the final dossier writer node."""

    async def writer_node(state: DeepVerifyGraphState) -> dict:
        draft = await write_dossier(
            llm=llm,
            question=state.original_question,
            claim_checks=state.claim_checks,
        )

        return {
            "draft": draft,
        }

    return writer_node