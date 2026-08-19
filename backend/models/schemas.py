from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str
    error_type: str | None = None


class HealthResponse(BaseModel):
    status: str
    checks: dict[str, Any]


class Citation(BaseModel):
    id: str | None = None
    title: str | None = None
    text: str
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LatencyBreakdown(BaseModel):
    stt_ms: float = 0.0
    query_processing_ms: float = 0.0
    query_embedding_ms: float = 0.0
    bm25_search_ms: float = 0.0
    vector_search_ms: float = 0.0
    hybrid_fusion_ms: float = 0.0
    reranking_ms: float = 0.0
    prompt_construction_ms: float = 0.0
    generation_ms: float = 0.0
    grounding_ms: float = 0.0
    total_pipeline_ms: float = 0.0


class GuardrailStatus(BaseModel):
    is_safe: bool = True
    is_on_topic: bool = True
    prompt_injection_detected: bool = False
    grounding_score: float = 1.0
    confidence_score: float = 1.0
    flag_reasons: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["What is machine learning?"])
    top_k: int = Field(default=5, ge=1, le=25)


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    guardrails: GuardrailStatus = Field(default_factory=GuardrailStatus)
    latency: LatencyBreakdown = Field(default_factory=LatencyBreakdown)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    id: str
    text: str
    score: float | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    latency_ms: float = 0.0
