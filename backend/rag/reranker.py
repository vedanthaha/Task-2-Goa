from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from .hybrid_retriever import HybridSearchResult


@dataclass
class RerankResult:
    results: list[HybridSearchResult]
    was_reranked: bool
    reason: str


class AdaptiveReranker:
    """
    Adaptive Reranker designed for low-latency RAG pipelines.
    Bypasses reranking when retrieval confidence is already decisive, 
    protecting the strict online latency SLA.
    """

    def __init__(
        self,
        confidence_bypass_threshold: float = 0.030,
        enable_reranking: bool = True,
    ) -> None:
        self.confidence_bypass_threshold = confidence_bypass_threshold
        self.enable_reranking = enable_reranking

    def rerank(
        self,
        query: str,
        candidates: list[HybridSearchResult],
        top_k: int = 5,
    ) -> RerankResult:
        if not candidates or not self.enable_reranking:
            return RerankResult(results=candidates[:top_k], was_reranked=False, reason="disabled_or_empty")

        top_cand = candidates[0]
        # If the top candidate is already highly decisive (high RRF score and present in both dense and BM25)
        is_decisive = (
            top_cand.fused_score >= self.confidence_bypass_threshold
            and top_cand.dense_rank is not None
            and top_cand.bm25_rank is not None
            and top_cand.dense_rank <= 2
            and top_cand.bm25_rank <= 2
        )

        if is_decisive:
            return RerankResult(
                results=candidates[:top_k],
                was_reranked=False,
                reason="high_confidence_bypass",
            )

        # Apply lightweight lexical-semantic cross-scoring
        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
        reranked = []

        for item in candidates:
            text_lower = item.text.lower()
            term_matches = sum(1 for t in query_terms if t in text_lower)
            match_ratio = term_matches / max(1, len(query_terms))

            # Combined rerank score: 60% fused RRF + 40% query term precision
            boosted_score = (item.fused_score * 30.0) * 0.6 + match_ratio * 0.4
            reranked.append((item, boosted_score))

        reranked.sort(key=lambda x: x[1], reverse=True)
        final_results = [item for item, _ in reranked[:top_k]]

        return RerankResult(
            results=final_results,
            was_reranked=True,
            reason="adaptive_cross_scoring",
        )
