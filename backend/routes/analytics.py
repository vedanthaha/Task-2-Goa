from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from rag.orchestrator import orchestrator
from services.latency_tracker import latency_tracker
from services.config import get_settings

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


class BenchmarkRequest(BaseModel):
    queries: list[str] = Field(
        default=[
            "What is machine learning?",
            "How does hybrid retrieval with RRF work?",
            "What are the benefits of solar photovoltaic systems?",
            "What is MSMARCO dataset?",
            "Tell me about speech recognition architecture.",
            "Explain deep neural network acoustic modeling",
            "How do container microservices communicate via gRPC?",
        ]
    )
    top_k: int = 5
    use_cache: bool = False


class BenchmarkResponse(BaseModel):
    total_queries: int
    p50_ms: float
    p70_ms: float
    p95_ms: float
    p100_ms: float
    mean_ms: float
    target_met: bool
    stages: dict[str, dict[str, float]] = Field(default_factory=dict)
    results: list[dict[str, Any]]


@router.get("/latency")
async def get_latency_metrics() -> dict[str, Any]:
    """Returns P50, P70, P95, and P100 latency percentiles across all historical queries."""
    total_metrics = latency_tracker.get_percentiles("total")
    stt_metrics = latency_tracker.get_percentiles("stt")
    retrieval_metrics = latency_tracker.get_percentiles("retrieval")
    generation_metrics = latency_tracker.get_percentiles("generation")
    guardrails_metrics = latency_tracker.get_percentiles("guardrails")

    return {
        "overall": {
            "p50_ms": total_metrics.p50_ms,
            "p70_ms": total_metrics.p70_ms,
            "p95_ms": total_metrics.p95_ms,
            "p100_ms": total_metrics.p100_ms,
            "mean_ms": total_metrics.mean_ms,
            "sample_count": total_metrics.sample_count,
            "target_ms": get_settings().target_latency_ms,
            "under_target": total_metrics.p50_ms <= get_settings().target_latency_ms if total_metrics.sample_count > 0 else True,
        },
        "stages": {
            "stt": {"p50_ms": stt_metrics.p50_ms, "mean_ms": stt_metrics.mean_ms},
            "retrieval": {"p50_ms": retrieval_metrics.p50_ms, "mean_ms": retrieval_metrics.mean_ms},
            "generation": {"p50_ms": generation_metrics.p50_ms, "mean_ms": generation_metrics.mean_ms},
            "guardrails": {"p50_ms": guardrails_metrics.p50_ms, "mean_ms": guardrails_metrics.mean_ms},
        },
    }


@router.post("/benchmark/run", response_model=BenchmarkResponse)
async def run_benchmark(payload: BenchmarkRequest) -> BenchmarkResponse:
    """Runs a batch evaluation benchmark over test questions, measures live latency percentiles, and reports real stage telemetry."""
    import numpy as np

    results = []
    latencies = []
    stage_collector: dict[str, list[float]] = {
        "query_processing": [],
        "vector_search": [],
        "bm25_search": [],
        "hybrid_fusion": [],
        "reranking": [],
        "generation": [],
        "grounding": [],
    }

    for q in payload.queries:
        if not q or not q.strip():
            continue
        res = await orchestrator.execute_query(
            query=q.strip(),
            top_k=payload.top_k,
            use_cache=payload.use_cache,
        )
        total_lat = res.latency.total_pipeline_ms
        latencies.append(total_lat)

        stage_collector["query_processing"].append(res.latency.query_processing_ms)
        stage_collector["vector_search"].append(res.latency.vector_search_ms)
        stage_collector["bm25_search"].append(res.latency.bm25_search_ms)
        stage_collector["hybrid_fusion"].append(res.latency.hybrid_fusion_ms)
        stage_collector["reranking"].append(res.latency.reranking_ms)
        stage_collector["generation"].append(res.latency.generation_ms)
        stage_collector["grounding"].append(res.latency.grounding_ms)

        results.append({
            "query": q,
            "answer_preview": res.answer[:140] + ("..." if len(res.answer) > 140 else ""),
            "citations_count": len(res.citations),
            "grounding_score": res.guardrails.grounding_score,
            "confidence_score": res.guardrails.confidence_score,
            "latency_ms": round(total_lat, 2),
            "stages": {
                "query_processing_ms": res.latency.query_processing_ms,
                "vector_search_ms": res.latency.vector_search_ms,
                "bm25_search_ms": res.latency.bm25_search_ms,
                "hybrid_fusion_ms": res.latency.hybrid_fusion_ms,
                "reranking_ms": res.latency.reranking_ms,
                "generation_ms": res.latency.generation_ms,
                "grounding_ms": res.latency.grounding_ms,
            },
        })

    arr = np.array(latencies) if latencies else np.array([0.0])
    p50 = round(float(np.percentile(arr, 50)), 2)
    p70 = round(float(np.percentile(arr, 70)), 2)
    p95 = round(float(np.percentile(arr, 95)), 2)
    p100 = round(float(np.max(arr)), 2)
    mean_val = round(float(np.mean(arr)), 2)

    # Compute real stage percentiles
    computed_stages: dict[str, dict[str, float]] = {}
    for st_name, vals in stage_collector.items():
        v_arr = np.array(vals) if vals else np.array([0.0])
        computed_stages[st_name] = {
            "p50_ms": round(float(np.percentile(v_arr, 50)), 2),
            "mean_ms": round(float(np.mean(v_arr)), 2),
            "p95_ms": round(float(np.percentile(v_arr, 95)), 2),
            "p100_ms": round(float(np.max(v_arr)), 2),
        }

    return BenchmarkResponse(
        total_queries=len(results),
        p50_ms=p50,
        p70_ms=p70,
        p95_ms=p95,
        p100_ms=p100,
        mean_ms=mean_val,
        target_met=p100 <= get_settings().target_latency_ms,
        stages=computed_stages,
        results=results,
    )
