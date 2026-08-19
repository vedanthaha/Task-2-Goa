from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    gemini_timeout_seconds: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "12.0"))
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "").strip()
    sarvam_model: str = os.getenv("SARVAM_MODEL", "saarika:v2.5").strip()

    dense_top_k: int = int(os.getenv("DENSE_TOP_K", "15"))
    bm25_top_k: int = int(os.getenv("BM25_TOP_K", "15"))
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    max_context_chars: int = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))

    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    target_latency_ms: int = int(float(os.getenv("TARGET_LATENCY_MS", "200")))


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
