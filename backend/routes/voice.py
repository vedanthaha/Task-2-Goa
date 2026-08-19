from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from services.sarvam_stt import sarvam_stt_service

router = APIRouter(prefix="/api/voice", tags=["voice"])
logger = logging.getLogger(__name__)


class TranscribeResponse(BaseModel):
    transcript: str
    language_code: str
    latency_ms: float = 0.0


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language_code: str = Form("en-IN"),
) -> TranscribeResponse:
    """Standalone Sarvam STT audio transcription endpoint."""
    import time
    start = time.perf_counter()
    content = await file.read()
    res = await sarvam_stt_service.transcribe(
        audio_content=content,
        filename=file.filename or "audio.wav",
        language_code=language_code,
    )
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return TranscribeResponse(
        transcript=res["transcript"],
        language_code=res["language_code"],
        latency_ms=elapsed_ms,
    )
