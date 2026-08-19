from __future__ import annotations

import logging
from typing import Any
from models.schemas import Citation, SearchResultItem
from services.llm_service import LLMService, NO_EVIDENCE_ANSWER
from .hybrid_retriever import HybridSearchResult

logger = logging.getLogger(__name__)


class GroundedGenerator:
    """Generates grounded responses with citation extraction and structured outputs."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService()

    async def generate_response(
        self,
        query: str,
        documents: list[HybridSearchResult],
    ) -> tuple[str, list[Citation]]:
        if not documents:
            return NO_EVIDENCE_ANSWER, []

        search_items = [
            SearchResultItem(
                id=doc.id,
                text=doc.text,
                score=doc.fused_score,
                source=doc.metadata.get("source", "MSMARCO-XI"),
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        raw_answer = await self.llm_service.answer_from_context(
            query=query,
            documents=search_items,
        )

        citations = [
            Citation(
                id=doc.id,
                title=doc.metadata.get("title") or f"MSMARCO Passage ({doc.id})",
                text=doc.text[:250] + ("..." if len(doc.text) > 250 else ""),
                score=doc.fused_score,
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        return raw_answer, citations
