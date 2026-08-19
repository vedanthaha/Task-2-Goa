from __future__ import annotations

import asyncio
import logging
from typing import Any
import requests

from models.schemas import SearchResultItem
from services.config import get_settings
from services.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

NO_EVIDENCE_ANSWER = "I could not find sufficient evidence in the retrieved knowledge base to answer your question."


class LLMService:
    def __init__(self) -> None:
        self._session = requests.Session()

    async def answer_from_context(
        self,
        query: str,
        documents: list[SearchResultItem],
        system_instructions: str | None = None,
    ) -> str:
        if not documents:
            return NO_EVIDENCE_ANSWER

        settings = get_settings()
        prompt = self._build_prompt(query=query, documents=documents)
        instructions = system_instructions or self._default_instructions()
        
        logger.info("Generating answer with Gemini model %s", settings.gemini_model)
        answer = await self._generate_text(instructions=instructions, prompt=prompt)
        return answer.strip() or NO_EVIDENCE_ANSWER

    async def _generate_text(
        self,
        instructions: str,
        prompt: str,
        temperature: float = 0.2,
    ) -> str:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY must be set in backend/.env.")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": instructions}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        params = {"key": settings.gemini_api_key}

        try:
            response = await asyncio.to_thread(
                self._session.post,
                url,
                params=params,
                json=payload,
                timeout=settings.gemini_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = getattr(exc.response, "text", "") if getattr(exc, "response", None) else ""
            message = f"Gemini request failed: {exc}"
            if detail:
                message = f"{message}. {detail[:500]}"
            raise ExternalServiceError(message) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Gemini returned a non-JSON response.") from exc

        candidates = data.get("candidates") or [{}]
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(str(part.get("text", "")) for part in parts)
        return text.strip()

    @staticmethod
    def _default_instructions() -> str:
        return (
            "You are a helpful, accurate voice assistant powered by retrieved knowledge. "
            "Answer the user's question directly, clearly, and concisely based strictly on the provided context passages. "
            f"If the context does not contain enough evidence, state: '{NO_EVIDENCE_ANSWER}' "
            "Do not make up facts or hallucinate beyond what is supported by the context."
        )

    @staticmethod
    def _build_prompt(query: str, documents: list[SearchResultItem]) -> str:
        max_context_chars = get_settings().max_context_chars
        sections: list[str] = []
        used_chars = 0

        for index, document in enumerate(documents, start=1):
            section = (
                f"[Source {index}] (ID: {document.id})\n"
                f"{document.text}\n"
            )
            if used_chars + len(section) > max_context_chars:
                remaining = max_context_chars - used_chars
                if remaining > 200:
                    sections.append(section[:remaining])
                break
            sections.append(section)
            used_chars += len(section)

        context = "\n---\n".join(sections)
        return f"User Question: {query}\n\nRetrieved Context Passages:\n{context}\n\nAnswer:"
