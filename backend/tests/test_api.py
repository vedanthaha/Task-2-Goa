from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient
from app import app
from services.sarvam_stt import sarvam_stt_service

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert data["checks"]["api"] == "ok"


def test_api_rag_query():
    response = client.post(
        "/api/rag/query",
        json={"query": "How does solar photovoltaic power work?", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "How does solar photovoltaic power work?"
    assert len(data["answer"]) > 0
    assert "latency" in data
    assert data["latency"]["total_pipeline_ms"] > 0
    assert "guardrails" in data
    assert len(data["citations"]) > 0


def test_api_rag_search():
    response = client.post(
        "/api/rag/search",
        json={"query": "voice recognition STT architecture", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 1
    assert "latency_ms" in data


def test_api_analytics_latency():
    response = client.get("/api/analytics/latency")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "stages" in data
    assert data["overall"]["target_ms"] == 200.0


def test_api_benchmark_run():
    response = client.post(
        "/api/analytics/benchmark/run",
        json={"queries": ["What is machine learning?", "What is solar energy?"], "top_k": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_queries"] == 2
    assert data["p50_ms"] > 0
    assert len(data["results"]) == 2


def test_api_voice_query_with_mocked_stt(monkeypatch):
    """Test voice upload -> Sarvam STT -> RAG query execution."""
    async def mock_transcribe(audio_content, filename="audio.wav", language_code="en-IN", model="saaras:v1"):
        return {
            "transcript": "How does hybrid retrieval with RRF work?",
            "language_code": language_code,
            "raw_response": {},
        }

    monkeypatch.setattr(sarvam_stt_service, "transcribe", mock_transcribe)

    fake_wav = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    response = client.post(
        "/api/rag/voice-query",
        files={"file": ("test.wav", fake_wav, "audio/wav")},
        data={"language_code": "en-IN", "top_k": "3"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "How does hybrid retrieval with RRF work?"
    assert len(data["citations"]) > 0
    assert data["latency"]["total_pipeline_ms"] > 0


def test_api_standalone_transcribe(monkeypatch):
    """Test standalone Sarvam STT transcription endpoint."""
    async def mock_transcribe(audio_content, filename="audio.wav", language_code="en-IN", model="saaras:v1"):
        return {
            "transcript": "Speech recognition transcription test",
            "language_code": language_code,
            "raw_response": {},
        }

    monkeypatch.setattr(sarvam_stt_service, "transcribe", mock_transcribe)

    fake_audio = io.BytesIO(b"dummy-audio-bytes")
    response = client.post(
        "/api/voice/transcribe",
        files={"file": ("audio.wav", fake_audio, "audio/wav")},
        data={"language_code": "en-IN"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "Speech recognition transcription test"
    assert data["language_code"] == "en-IN"
    assert data["latency_ms"] >= 0
