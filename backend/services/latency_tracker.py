from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
import numpy as np

from models.schemas import LatencyBreakdown


class StageTimer:
    """Microsecond-precision context manager for pipeline stage timing."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> StageTimer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.elapsed_ms = round((time.perf_counter() - self.start_time) * 1000, 2)


@dataclass
class LatencyPercentiles:
    p50_ms: float = 0.0
    p70_ms: float = 0.0
    p95_ms: float = 0.0
    p100_ms: float = 0.0
    mean_ms: float = 0.0
    sample_count: int = 0


class LatencyTracker:
    """Records pipeline stage latencies and calculates P50, P70, P100 metrics."""

    def __init__(self, max_history: int = 1000) -> None:
        self.max_history = max_history
        self._history: deque[float] = deque(maxlen=max_history)
        self._stage_history: dict[str, deque[float]] = {
            "stt": deque(maxlen=max_history),
            "query_processing": deque(maxlen=max_history),
            "retrieval": deque(maxlen=max_history),
            "generation": deque(maxlen=max_history),
            "guardrails": deque(maxlen=max_history),
            "total": deque(maxlen=max_history),
        }

    def record(self, breakdown: LatencyBreakdown) -> None:
        self._history.append(breakdown.total_pipeline_ms)
        self._stage_history["stt"].append(breakdown.stt_ms)
        self._stage_history["query_processing"].append(breakdown.query_processing_ms)
        retrieval_total = breakdown.vector_search_ms + breakdown.bm25_search_ms + breakdown.hybrid_fusion_ms + breakdown.reranking_ms
        self._stage_history["retrieval"].append(retrieval_total)
        self._stage_history["generation"].append(breakdown.generation_ms)
        self._stage_history["guardrails"].append(breakdown.grounding_ms)
        self._stage_history["total"].append(breakdown.total_pipeline_ms)

    def get_percentiles(self, stage: str = "total") -> LatencyPercentiles:
        data = self._stage_history.get(stage, self._history)
        if not data:
            return LatencyPercentiles()

        arr = np.array(list(data))
        return LatencyPercentiles(
            p50_ms=round(float(np.percentile(arr, 50)), 2),
            p70_ms=round(float(np.percentile(arr, 70)), 2),
            p95_ms=round(float(np.percentile(arr, 95)), 2),
            p100_ms=round(float(np.max(arr)), 2),
            mean_ms=round(float(np.mean(arr)), 2),
            sample_count=len(arr),
        )


latency_tracker = LatencyTracker()
