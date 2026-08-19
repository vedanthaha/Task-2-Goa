from __future__ import annotations

import base64
import logging
import os
from typing import Any
import httpx

from services.config import get_settings
from services.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)


def detect_audio_mime(content: bytes) -> tuple[str, str]:
    """Detects MIME type and extension from audio file magic header bytes."""
    if content.startswith(b"RIFF"):
        return "audio.wav", "audio/wav"
    elif content.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio.webm", "audio/webm"
    elif content.startswith(b"OggS"):
        return "audio.ogg", "audio/ogg"
    elif content.startswith(b"ID3") or content.startswith(b"\xff\xfb"):
        return "audio.mp3", "audio/mpeg"
    elif len(content) > 8 and content[4:8] == b"ftyp":
        return "audio.mp4", "audio/mp4"
    return "audio.wav", "audio/wav"


class SarvamSTTService:
    """Dedicated asynchronous client for Sarvam AI Speech-to-Text API."""

    BASE_URL = "https://api.sarvam.ai/speech-to-text"

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def transcribe(
        self,
        audio_content: bytes,
        filename: str = "audio.wav",
        language_code: str = "en-IN",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Transcribes audio bytes using Sarvam STT API."""
        settings = get_settings()
        if not settings.sarvam_api_key:
            raise ConfigurationError(
                "SARVAM_API_KEY is not configured in backend/.env. Speech-to-text requires a valid Sarvam API key."
            )

        if not audio_content or len(audio_content) == 0:
            raise ExternalServiceError("Audio content is empty.")

        selected_model = model or os.getenv("SARVAM_MODEL", "saarika:v2.5").strip()
        lang = language_code if language_code and language_code != "auto" else "en-IN"

        auto_fname, mime_type = detect_audio_mime(audio_content)
        final_fname = filename if ("." in filename) else auto_fname

        headers = {
            "api-subscription-key": settings.sarvam_api_key,
        }

        # Multipart payload with detected mime type
        files = {
            "file": (final_fname, audio_content, mime_type),
        }
        data = {
            "language_code": lang,
            "model": selected_model,
        }

        logger.info("Calling Sarvam STT: bytes=%d, mime=%s, model=%s, lang=%s", len(audio_content), mime_type, selected_model, lang)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text[:400] if exc.response else ""
            logger.error("Sarvam STT HTTP error: %s (%s)", exc, error_detail)
            raise ExternalServiceError(f"Sarvam STT failed ({exc.response.status_code}): {error_detail}") from exc
        except httpx.RequestError as exc:
            logger.error("Sarvam STT network error: %s", exc)
            raise ExternalServiceError(f"Sarvam STT connection error: {exc}") from exc
        except Exception as exc:
            logger.error("Sarvam STT unexpected error: %s", exc)
            raise ExternalServiceError(f"Sarvam STT transcription failed: {exc}") from exc

        transcript = payload.get("transcript", "")
        detected_lang = payload.get("language_code", lang)
        logger.info("Sarvam STT success: transcript=%r, detected_lang=%s", transcript, detected_lang)

        return {
            "transcript": transcript.strip(),
            "language_code": detected_lang,
            "raw_response": payload,
        }

    async def transcribe_base64(
        self,
        base64_audio: str,
        language_code: str = "en-IN",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Transcribes base64-encoded audio."""
        if "," in base64_audio:
            base64_audio = base64_audio.split(",", 1)[1]
        raw_bytes = base64.b64decode(base64_audio)
        return await self.transcribe(raw_bytes, language_code=language_code, model=model)


sarvam_stt_service = SarvamSTTService()
