export interface Citation {
  id?: string | null;
  title?: string | null;
  text: string;
  score?: number | null;
  metadata?: Record<string, unknown>;
}

export interface LatencyBreakdown {
  stt_ms: number;
  query_processing_ms: number;
  query_embedding_ms: number;
  bm25_search_ms: number;
  vector_search_ms: number;
  hybrid_fusion_ms: number;
  reranking_ms: number;
  prompt_construction_ms: number;
  generation_ms: number;
  grounding_ms: number;
  total_pipeline_ms: number;
}

export interface GuardrailStatus {
  is_safe: boolean;
  is_on_topic: boolean;
  prompt_injection_detected: boolean;
  grounding_score: number;
  confidence_score: number;
  flag_reasons: string[];
}

export interface QueryResponse {
  query: string;
  answer: string;
  citations: Citation[];
  guardrails: GuardrailStatus;
  latency: LatencyBreakdown;
}

export interface HealthResponse {
  status: string;
  checks: {
    api?: string;
    gemini_configured?: boolean;
    sarvam_configured?: boolean;
    target_latency_ms?: number;
    [key: string]: unknown;
  };
}

export interface BenchmarkRecord {
  id: string;
  category: string;
  language: string;
  query: string;
  answer_preview: string;
  citations_count: number;
  is_safe: boolean;
  is_on_topic: boolean;
  prompt_injection: boolean;
  grounding_score: number;
  confidence_score: number;
  query_processing_ms: number;
  vector_search_ms: number;
  bm25_search_ms: number;
  hybrid_fusion_ms: number;
  reranking_ms: number;
  generation_ms: number;
  grounding_ms: number;
  total_ms: number;
}

export interface PercentileStats {
  p50: number;
  p70: number;
  p90: number;
  p95: number;
  p100: number;
  mean: number;
  min: number;
}

export interface CategoryStat {
  percentiles: PercentileStats;
  accuracy_pct: number;
  query_count: number;
}

export interface BenchmarkResponse {
  total_queries: number;
  p50_ms: number;
  p70_ms: number;
  p95_ms: number;
  p100_ms: number;
  mean_ms: number;
  target_met: boolean;
  results: Array<{
    query: string;
    answer_preview: string;
    citations_count: number;
    grounding_score: number;
    confidence_score: number;
    latency_ms: number;
  }>;
}

export type InteractionState =
  | "idle"
  | "listening"
  | "transcribing"
  | "retrieving"
  | "generating"
  | "complete"
  | "error";
