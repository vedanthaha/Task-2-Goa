from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from models.schemas import (
    Citation,
    GuardrailStatus,
    LatencyBreakdown,
    QueryResponse,
    SearchResultItem,
)
from services.config import get_settings, BASE_DIR
from services.exceptions import AppError, ConfigurationError, ExternalServiceError
from services.latency_tracker import latency_tracker
from services.sarvam_stt import SarvamSTTService, sarvam_stt_service

from .embeddings import FastDenseEmbedder
from .vector_store import VectorStore
from .bm25_search import BM25Index
from .hybrid_retriever import HybridSearchResult, HybridRetriever
from .reranker import AdaptiveReranker
from .guardrails import SafetyGuard, GuardrailResult
from .grounding import GroundingChecker, GroundingResult
from .generator import GroundedGenerator

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """
    Central orchestration harness for the Voice-Enabled RAG system.
    Coordinating STT -> Query Guardrails -> Parallel Hybrid Retrieval -> 
    Adaptive Reranking -> Grounded LLM Generation -> Hallucination Checker -> Latency Telemetry.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        bm25_index: BM25Index | None = None,
        stt_service: SarvamSTTService | None = None,
        data_dir: Path | str | None = None,
    ) -> None:
        self.data_dir = Path(data_dir or BASE_DIR / "data")
        self.stt_service = stt_service or sarvam_stt_service
        self.safety_guard = SafetyGuard()
        self.grounding_checker = GroundingChecker()
        self.reranker = AdaptiveReranker()
        self.generator = GroundedGenerator()

        # Initialize or load indexes
        self.vector_store = vector_store or VectorStore()
        self.bm25_index = bm25_index or BM25Index()
        self._load_or_bootstrap_indexes()

        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_index=self.bm25_index,
        )

    def _load_or_bootstrap_indexes(self) -> None:
        dense_dir = self.data_dir / "dense_index"
        bm25_dir = self.data_dir / "bm25_index"

        loaded_dense = self.vector_store.load(dense_dir)
        loaded_bm25 = self.bm25_index.load(bm25_dir)

        if not loaded_dense or not loaded_bm25:
            logger.info("Pre-computed indexes not found at %s. Bootstrapping initial index...", self.data_dir)
            from indexing.dataset_loader import MSMARCODataLoader
            from indexing.chunkers import SentenceAwareChunker

            loader = MSMARCODataLoader()
            docs = loader.load_documents()
            chunker = SentenceAwareChunker()
            
            all_chunks = []
            for d in docs:
                all_chunks.extend(chunker.chunk(d.document_id, d.text, d.language, {"title": d.title, "url": d.url}))

            ids = [c.chunk_id for c in all_chunks]
            texts = [c.text for c in all_chunks]
            metas = [{"chunk_id": c.chunk_id, "document_id": c.document_id, "language": c.language, **c.metadata} for c in all_chunks]

            self.vector_store.add_documents(ids, texts, metas)
            self.bm25_index.add_documents(ids, texts, metas)

            self.vector_store.save(dense_dir)
            self.bm25_index.save(bm25_dir)
            logger.info("Successfully bootstrapped in-memory and disk indexes with %d chunks.", len(all_chunks))

    async def execute_query(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        use_cache: bool = True,
        rerank_mode: str = "adaptive",
    ) -> QueryResponse:
        """Executes the full online RAG inference pipeline with high-resolution latency tracing."""
        t_total_start = time.perf_counter_ns()
        settings = get_settings()
        breakdown = LatencyBreakdown()

        # 1. Query Preprocessing & Safety Validation
        t_qp_start = time.perf_counter_ns()
        guard_res = self.safety_guard.validate_query(query)
        breakdown.query_processing_ms = round((time.perf_counter_ns() - t_qp_start) / 1_000_000, 3)

        if not guard_res.passed:
            breakdown.total_pipeline_ms = round((time.perf_counter_ns() - t_total_start) / 1_000_000, 3)
            
            if guard_res.is_empty:
                return QueryResponse(
                    query=query or "(Silence / No speech)",
                    answer="I couldn't hear or detect clear speech from your audio. Please click the microphone button, speak your question clearly, and click again when done.",
                    citations=[],
                    guardrails=GuardrailStatus(
                        is_safe=True,
                        is_on_topic=False,
                        prompt_injection_detected=False,
                        confidence_score=0.0,
                        flag_reasons=["Empty speech / silence detected"],
                    ),
                    latency=breakdown,
                )

            logger.warning("Query rejected by safety guardrail: %s", guard_res.flag_reasons)
            return QueryResponse(
                query=query,
                answer="I cannot fulfill this request because it violated safety policies or prompt injection defenses.",
                citations=[],
                guardrails=GuardrailStatus(
                    is_safe=guard_res.is_safe,
                    is_on_topic=guard_res.is_on_topic,
                    prompt_injection_detected=guard_res.prompt_injection_detected,
                    confidence_score=0.0,
                    flag_reasons=guard_res.flag_reasons,
                ),
                latency=breakdown,
            )

        # 2. Parallel Hybrid Retrieval (Dense + BM25 with RRF)
        hybrid_candidates, ret_timing = await self.retriever.search_with_timing(
            query=query,
            top_k=top_k * 2,
            dense_top_k=settings.dense_top_k,
            bm25_top_k=settings.bm25_top_k,
            filters=filters,
            use_cache=use_cache,
        )
        breakdown.query_embedding_ms = ret_timing.embedding_ms
        breakdown.vector_search_ms = ret_timing.vector_search_ms
        breakdown.bm25_search_ms = ret_timing.bm25_search_ms
        breakdown.hybrid_fusion_ms = ret_timing.fusion_ms

        # 3. Retrieval Confidence Check
        logger.info(f"Hybrid candidates: {[c.id for c in hybrid_candidates]}")
        t_conf_start = time.perf_counter_ns()
        conf_res = self.safety_guard.validate_retrieval_confidence(query, hybrid_candidates)
        conf_time = (time.perf_counter_ns() - t_conf_start) / 1_000_000

        # 4. Latency-Aware Reranking
        t_rerank_start = time.perf_counter_ns()
        if rerank_mode == "none":
            final_docs = hybrid_candidates[:top_k]
        elif rerank_mode == "always":
            rerank_res = self.reranker.rerank(query=query, candidates=hybrid_candidates, top_k=top_k)
            final_docs = rerank_res.results
        else:  # adaptive
            rerank_res = self.reranker.rerank(query=query, candidates=hybrid_candidates, top_k=top_k)
            final_docs = rerank_res.results
        breakdown.reranking_ms = round((time.perf_counter_ns() - t_rerank_start) / 1_000_000, 3)

        # 5. Prompt Construction & Grounded Generation (latency-budgeted)
        t_gen_start = time.perf_counter_ns()
        elapsed_so_far_s = (t_gen_start - t_total_start) / 1_000_000_000
        # Reserve 30ms buffer for retrieval, reranking, grounding verification, and event loop overhead
        target_max_s = (settings.target_latency_ms - 30.0) / 1000.0
        remaining_budget_s = max(0, target_max_s - elapsed_so_far_s)
        try:
            answer, citations = await self.generator.generate_response(
                query=query,
                documents=final_docs,
                use_cache=use_cache,
                deadline_seconds=None,
            )
            if not answer or answer.strip() == "":
                answer = "I could not find sufficient evidence in the retrieved knowledge base to answer your question."
        except Exception as exc:
            logger.error("LLM Generation error: %s", exc)
            answer = "I could not find sufficient evidence in the retrieved knowledge base to answer your question."
            citations = [
                Citation(
                    id=doc.id,
                    title=doc.metadata.get("title", "MSMARCO Document"),
                    text=doc.text[:250],
                    score=doc.fused_score,
                    metadata=doc.metadata,
                )
                for doc in final_docs
            ]
        breakdown.generation_ms = round((time.perf_counter_ns() - t_gen_start) / 1_000_000, 3)

        if not conf_res.passed and citations:
            citations = []
            answer = f"Note: I could not find exact matching documents in the MSMARCO-XI dataset for this query.\n\n{answer}"

        # 6. Grounding Verification
        t_ground_start = time.perf_counter_ns()
        grounding_res = self.grounding_checker.verify(answer=answer, retrieved_docs=final_docs)
        breakdown.grounding_ms = round(((time.perf_counter_ns() - t_ground_start) / 1_000_000) + conf_time, 3)

        breakdown.total_pipeline_ms = round((time.perf_counter_ns() - t_total_start) / 1_000_000, 3)
        latency_tracker.record(breakdown)

        return QueryResponse(
            query=query,
            answer=answer,
            citations=citations,
            guardrails=GuardrailStatus(
                is_safe=True,
                is_on_topic=conf_res.passed,
                prompt_injection_detected=False,
                grounding_score=grounding_res.grounding_score,
                confidence_score=conf_res.confidence_score,
                flag_reasons=conf_res.flag_reasons if not conf_res.passed else [],
            ),
            latency=breakdown,
        )

    async def execute_voice_query(
        self,
        audio_bytes: bytes,
        language_code: str = "unknown",
        top_k: int = 5,
    ) -> tuple[str, QueryResponse]:
        """Transcribes audio with Sarvam STT and routes transcript through RAG pipeline."""
        t_stt_start = time.perf_counter_ns()
        stt_result = await self.stt_service.transcribe(
            audio_content=audio_bytes,
            language_code=language_code,
        )
        transcript = stt_result.get("transcript", "").strip()
        stt_elapsed_ms = (time.perf_counter_ns() - t_stt_start) / 1_000_000
        
        response = await self.execute_query(query=transcript, top_k=top_k)
        response.latency.stt_ms = round(stt_elapsed_ms, 3)
        response.latency.total_pipeline_ms = round(response.latency.total_pipeline_ms + stt_elapsed_ms, 3)

        return transcript, response

    def clear_cache(self) -> None:
        """Clears all in-memory caches across retriever and generator."""
        self.retriever.clear_cache()
        if hasattr(self.generator.llm_service, "clear_cache"):
            self.generator.llm_service.clear_cache()


# Global instance
orchestrator = RAGOrchestrator()
