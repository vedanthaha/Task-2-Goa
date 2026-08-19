# HH Goa 2026 — Voice RAG Backend Service

FastAPI service delivering sub-200ms hybrid retrieval, Sarvam STT transcription, guardrails, and grounded response synthesis over `ai4bharat/MSMARCO-XI`.

## Endpoints

- `GET /health` — Health and provider readiness telemetry.
- `POST /api/rag/query` — End-to-end RAG query execution with citations, guardrails, and latency metrics.
- `POST /api/rag/search` — Direct hybrid search over indexed MSMARCO-XI passages.
