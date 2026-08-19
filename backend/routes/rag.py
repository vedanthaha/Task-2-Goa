from __future__ import annotations

import logging
import time
from fastapi import APIRouter, File, Form, UploadFile

from models.schemas import (
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from rag.orchestrator import orchestrator

router = APIRouter(prefix="/api/rag", tags=["rag"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query_rag(payload: QueryRequest) -> QueryResponse:
    """Executes full online RAG inference pipeline on text query."""
    logger.info("RAG query received: %r (top_k=%d)", payload.query, payload.top_k)
    return await orchestrator.execute_query(query=payload.query, top_k=payload.top_k)


@router.post("/voice-query", response_model=QueryResponse)
async def voice_query_rag(
    file: UploadFile = File(...),
    language_code: str = Form("en-IN"),
    top_k: int = Form(5),
) -> QueryResponse:
    """Accepts voice audio file, transcribes with Sarvam STT, and executes RAG pipeline."""
    logger.info("Voice query received: filename=%s, lang=%s", file.filename, language_code)
    audio_content = await file.read()
    transcript, response = await orchestrator.execute_voice_query(
        audio_bytes=audio_content,
        language_code=language_code,
        top_k=int(top_k),
    )
    logger.info("Voice transcribed: %r (total latency=%.2fms)", transcript, response.latency.total_pipeline_ms)
    return response


@router.post("/search", response_model=SearchResponse)
async def search_rag(payload: SearchRequest) -> SearchResponse:
    """Executes parallel hybrid search over indexed MSMARCO-XI corpus."""
    start_time = time.perf_counter()
    candidates = await orchestrator.retriever.search(query=payload.query, top_k=payload.top_k)
    latency_ms = (time.perf_counter() - start_time) * 1000

    results = [
        SearchResultItem(
            id=c.id,
            text=c.text,
            score=c.fused_score,
            source=c.metadata.get("source", "MSMARCO-XI"),
            metadata=c.metadata,
        )
        for c in candidates
    ]

    return SearchResponse(
        query=payload.query,
        results=results,
        latency_ms=round(latency_ms, 2),
    )
