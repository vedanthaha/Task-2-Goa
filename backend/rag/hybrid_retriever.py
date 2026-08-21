from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from .vector_store import VectorStore
from .bm25_search import BM25Index


@dataclass
class HybridSearchResult:
    id: str
    text: str
    fused_score: float
    dense_score: float | None = None
    bm25_score: float | None = None
    dense_rank: int | None = None
    bm25_rank: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalTiming:
    embedding_ms: float = 0.0
    vector_search_ms: float = 0.0
    bm25_search_ms: float = 0.0
    fusion_ms: float = 0.0
    total_retrieval_ms: float = 0.0


class HybridRetriever:
    """
    Hybrid Retriever executing Dense Vector search and Lexical BM25 search in parallel, 
    fusing rankings using Reciprocal Rank Fusion (RRF) with sub-millisecond stage instrumentation.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_index: BM25Index,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0,
        cache_capacity: int = 2048,
    ) -> None:
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.cache_capacity = cache_capacity
        self._cache: OrderedDict[str, list[HybridSearchResult]] = OrderedDict()
        self._cache_lock = Lock()

    async def search_with_timing(
        self,
        query: str,
        top_k: int = 5,
        dense_top_k: int = 15,
        bm25_top_k: int = 15,
        filters: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> tuple[list[HybridSearchResult], RetrievalTiming]:
        start_total = time.perf_counter_ns()
        timing = RetrievalTiming()

        cache_key = f"{query.strip().lower()}:{top_k}:{dense_top_k}:{bm25_top_k}:{str(filters)}"
        if use_cache:
            with self._cache_lock:
                if cache_key in self._cache:
                    cached_results = self._cache[cache_key]
                    self._cache.move_to_end(cache_key)
                    timing.total_retrieval_ms = round((time.perf_counter_ns() - start_total) / 1_000_000, 3)
                    return cached_results, timing

        # Run embedding + dense search and lexical search concurrently
        async def run_dense():
            t0 = time.perf_counter_ns()
            res = await asyncio.to_thread(self.vector_store.search, query, top_k=dense_top_k, filters=filters)
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return res, elapsed

        async def run_bm25():
            t0 = time.perf_counter_ns()
            res = await asyncio.to_thread(self.bm25_index.search, query, top_k=bm25_top_k, filters=filters)
            elapsed = (time.perf_counter_ns() - t0) / 1_000_000
            return res, elapsed

        import logging
        logger = logging.getLogger(__name__)

        results = await asyncio.gather(run_dense(), run_bm25(), return_exceptions=True)

        dense_results, dense_time = [], 0.0
        if isinstance(results[0], Exception):
            logger.warning("Dense search failed: %s", results[0])
        else:
            dense_results, dense_time = results[0]

        bm25_results, bm25_time = [], 0.0
        if isinstance(results[1], Exception):
            logger.warning("BM25 search failed: %s", results[1])
        else:
            bm25_results, bm25_time = results[1]

        timing.vector_search_ms = round(dense_time, 3)
        timing.bm25_search_ms = round(bm25_time, 3)

        # Fusion
        start_fusion = time.perf_counter_ns()
        candidates: dict[str, dict[str, Any]] = {}

        for rank, res in enumerate(dense_results, start=1):
            candidates[res.id] = {
                "id": res.id,
                "text": res.text,
                "metadata": res.metadata,
                "dense_score": res.score,
                "dense_rank": rank,
                "bm25_score": None,
                "bm25_rank": None,
                "rrf_score": self.dense_weight / (self.rrf_k + rank),
            }

        for rank, res in enumerate(bm25_results, start=1):
            if res.id in candidates:
                candidates[res.id]["bm25_score"] = res.score
                candidates[res.id]["bm25_rank"] = rank
                candidates[res.id]["rrf_score"] += self.bm25_weight / (self.rrf_k + rank)
            else:
                candidates[res.id] = {
                    "id": res.id,
                    "text": res.text,
                    "metadata": res.metadata,
                    "dense_score": None,
                    "dense_rank": None,
                    "bm25_score": res.score,
                    "bm25_rank": rank,
                    "rrf_score": self.bm25_weight / (self.rrf_k + rank),
                }

        sorted_candidates = sorted(candidates.values(), key=lambda x: x["rrf_score"], reverse=True)
        top_candidates = sorted_candidates[:top_k]

        results = [
            HybridSearchResult(
                id=c["id"],
                text=c["text"],
                fused_score=round(c["rrf_score"], 4),
                dense_score=round(c["dense_score"], 4) if c["dense_score"] is not None else None,
                bm25_score=round(c["bm25_score"], 4) if c["bm25_score"] is not None else None,
                dense_rank=c["dense_rank"],
                bm25_rank=c["bm25_rank"],
                metadata=c["metadata"],
            )
            for c in top_candidates
        ]

        timing.fusion_ms = round((time.perf_counter_ns() - start_fusion) / 1_000_000, 3)
        timing.total_retrieval_ms = round((time.perf_counter_ns() - start_total) / 1_000_000, 3)

        if use_cache:
            with self._cache_lock:
                self._cache[cache_key] = results
                if len(self._cache) > self.cache_capacity:
                    self._cache.popitem(last=False)

        return results, timing

    async def search(
        self,
        query: str,
        top_k: int = 5,
        dense_top_k: int = 15,
        bm25_top_k: int = 15,
        filters: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> list[HybridSearchResult]:
        results, _ = await self.search_with_timing(
            query=query,
            top_k=top_k,
            dense_top_k=dense_top_k,
            bm25_top_k=bm25_top_k,
            filters=filters,
            use_cache=use_cache,
        )
        return results

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()
