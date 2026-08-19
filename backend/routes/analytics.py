from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from rag.orchestrator import orchestrator
from services.latency_tracker import latency_tracker

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
        ]
    )
    top_k: int = 5


class BenchmarkResponse(BaseModel):
    total_queries: int
    p50_ms: float
    p70_ms: float
    p95_ms: float
    p100_ms: float
    mean_ms: float
    target_met: bool
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
            "target_ms": 200.0,
            "under_200ms_target": total_metrics.p50_ms <= 200.0 if total_metrics.sample_count > 0 else True,
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
    """Runs a batch evaluation benchmark over test questions, measures latency percentiles, and reports results."""
    import time
    import numpy as np

    results = []
    latencies = []

    for q in payload.queries:
        res = await orchestrator.execute_query(query=q, top_k=payload.top_k)
        latencies.append(res.latency.total_pipeline_ms)
        results.append({
            "query": q,
            "answer_preview": res.answer[:120] + "...",
            "citations_count": len(res.citations),
            "grounding_score": res.guardrails.grounding_score,
            "confidence_score": res.guardrails.confidence_score,
            "latency_ms": res.latency.total_pipeline_ms,
        })

    arr = np.array(latencies) if latencies else np.array([0.0])
    p50 = round(float(np.percentile(arr, 50)), 2)
    p70 = round(float(np.percentile(arr, 70)), 2)
    p95 = round(float(np.percentile(arr, 95)), 2)
    p100 = round(float(np.max(arr)), 2)
    mean_val = round(float(np.mean(arr)), 2)

    return BenchmarkResponse(
        total_queries=len(payload.queries),
        p50_ms=p50,
        p70_ms=p70,
        p95_ms=p95,
        p100_ms=p100,
        mean_ms=mean_val,
        target_met=p50 <= 200.0,
        results=results,
    )
