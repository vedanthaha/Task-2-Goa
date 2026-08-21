from __future__ import annotations

import asyncio
import logging
import time
import httpx

from models.schemas import SearchResultItem
from services.config import get_settings
from services.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

NO_EVIDENCE_ANSWER = (
    "I could not find sufficient evidence in the retrieved knowledge base to answer your question."
)


class LLMService:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def close(self) -> None:
        await self._client.aclose()

    async def answer_from_context(
        self,
        query: str,
        documents: list[SearchResultItem],
        system_instructions: str | None = None,
    ) -> str:
        if not documents:
            return NO_EVIDENCE_ANSWER

        settings = get_settings()
        logger.info("Generating answer with Groq model: %s", settings.groq_model)
        prompt = self._build_prompt(query=query, documents=documents)
        instructions = system_instructions or self._default_instructions()
        answer = await self._generate_text(instructions=instructions, prompt=prompt)
        return answer.strip() or NO_EVIDENCE_ANSWER

    async def _generate_text(
        self,
        instructions: str,
        prompt: str,
        temperature: float = 0.2,
    ) -> str:
        settings = get_settings()
        if not settings.groq_api_key:
            raise ConfigurationError("GROQ_API_KEY must be set in backend/.env.")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 512,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                t0 = time.time()
                logger.debug("POST %s model=%s attempt=%d", url, settings.groq_model, attempt + 1)

                response = await self._client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=settings.groq_timeout_seconds,
                )

                elapsed_ms = (time.time() - t0) * 1000
                logger.info("Groq response: %.1fms (status=%d)", elapsed_ms, response.status_code)

                response.raise_for_status()
                break

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    wait = 3 + attempt * 2
                    logger.warning("Groq rate limit (429). Retrying in %ds...", wait)
                    await asyncio.sleep(wait)
                    continue
                detail = exc.response.text
                raise ExternalServiceError(
                    f"Groq request failed ({exc.response.status_code}): {detail[:400]}"
                ) from exc
            except httpx.RequestError as exc:
                raise ExternalServiceError(f"Groq network error: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Groq returned non-JSON response.") from exc

        choices = data.get("choices") or [{}]
        content = choices[0].get("message", {}).get("content", "")
        return content.strip()

    @staticmethod
    def _default_instructions() -> str:
        return (
            "You are a concise, accurate voice assistant powered by retrieved knowledge. "
            "Answer the user's question directly and briefly based strictly on the provided context. "
            f"If the context lacks sufficient evidence, respond: '{NO_EVIDENCE_ANSWER}' "
            "Do not fabricate facts. Keep answers short (2-4 sentences max)."
        )

    @staticmethod
    def _build_prompt(query: str, documents: list[SearchResultItem]) -> str:
        max_context_chars = get_settings().max_context_chars
        sections: list[str] = []
        used_chars = 0

        for index, doc in enumerate(documents, start=1):
            section = f"[Source {index}] (ID: {doc.id})\n{doc.text}\n"
            if used_chars + len(section) > max_context_chars:
                remaining = max_context_chars - used_chars
                if remaining > 200:
                    sections.append(section[:remaining])
                break
            sections.append(section)
            used_chars += len(section)

        context = "\n---\n".join(sections)
        return f"User Question: {query}\n\nRetrieved Context:\n{context}\n\nAnswer:"
