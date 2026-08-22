import { BenchmarkResponse, HealthResponse, QueryResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendTextQuery(
  query: string,
  top_k: number = 5
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/api/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Query failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendVoiceQuery(
  audioBlob: Blob,
  languageCode: string = "en-IN",
  top_k: number = 5
): Promise<QueryResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "voice_recording.wav");
  formData.append("language_code", languageCode);
  formData.append("top_k", String(top_k));

  const res = await fetch(`${API_BASE_URL}/api/rag/voice-query`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Voice query failed: ${res.statusText}`);
  }
  return res.json();
}

export async function runBenchmark(
  queries?: string[],
  top_k: number = 5,
  useCache: boolean = false
): Promise<BenchmarkResponse> {
  const payload = queries
    ? { queries, top_k, use_cache: useCache }
    : { top_k, use_cache: useCache };
  const res = await fetch(`${API_BASE_URL}/api/analytics/benchmark/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Benchmark failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchLatencyMetrics(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE_URL}/api/analytics/latency`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch latency metrics: ${res.statusText}`);
  }
  return res.json();
}
