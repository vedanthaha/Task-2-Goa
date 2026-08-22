from __future__ import annotations

import asyncio
import logging
import re
import time
from collections import OrderedDict
from threading import Lock
import httpx

from models.schemas import SearchResultItem
from services.config import get_settings
from services.exceptions import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)

NO_EVIDENCE_ANSWER = (
    "I could not find sufficient evidence in the retrieved knowledge base to answer your question."
)


class LLMService:
    """
    Ultra-low-latency Grounded LLM Generation Service with:
    - Persistent HTTP connection pooling and keep-alive
    - High-performance in-memory LRU Query-Answer caching
    - Concise grounded prompt construction
    - Microsecond-budgeted extractive synthesis fallback to guarantee < 200ms SLA
    """

    def __init__(self, cache_capacity: int = 4096) -> None:
        limits = httpx.Limits(
            max_keepalive_connections=30,
            max_connections=50,
            keepalive_expiry=60.0,
        )
        self._client = httpx.AsyncClient(limits=limits, timeout=2.5)
        self._cache_capacity = cache_capacity
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._cache_lock = Lock()

    async def close(self) -> None:
        await self._client.aclose()

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    async def warmup(self) -> None:
        """Pre-warms the HTTP connection to Groq API endpoint."""
        settings = get_settings()
        if not settings.groq_api_key:
            return
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.groq_model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            }
            await self._client.post(url, headers=headers, json=payload, timeout=2.0)
            logger.info("Groq HTTP connection pool pre-warmed successfully.")
        except Exception as exc:
            logger.debug("Groq warmup skipped: %s", exc)

    async def answer_from_context(
        self,
        query: str,
        documents: list[SearchResultItem],
        system_instructions: str | None = None,
        use_cache: bool = True,
        deadline_seconds: float | None = None,
    ) -> str:
        if not documents:
            return NO_EVIDENCE_ANSWER

        # Check Cache
        norm_query = query.strip().lower()
        doc_signature = ":".join(d.id for d in documents[:3])
        cache_key = f"{norm_query}|{doc_signature}"

        if use_cache:
            with self._cache_lock:
                if cache_key in self._cache:
                    cached_ans = self._cache[cache_key]
                    self._cache.move_to_end(cache_key)
                    return cached_ans

        settings = get_settings()
        instructions = system_instructions or self._default_instructions()
        prompt = self._build_prompt(query=query, documents=documents)

        # Generate answer with latency-budgeted Groq call or extractive synthesis fallback
        try:
            coro = self._generate_text(instructions=instructions, prompt=prompt)
            if deadline_seconds is not None and deadline_seconds > 0.01:
                answer = await asyncio.wait_for(coro, timeout=deadline_seconds)
            else:
                # No budget left — skip LLM entirely, use extractive synthesis
                answer = ""
            answer = self._clean_llm_response(answer) if answer else ""
        except asyncio.TimeoutError:
            logger.info("Groq LLM exceeded latency budget (%.0fms). Using extractive synthesis.",
                        (deadline_seconds or 0) * 1000)
            answer = self._synthesize_extractive_answer(query=query, documents=documents)
        except Exception as exc:
            logger.warning("External LLM generation error (%s). Using extractive synthesis.", exc)
            answer = self._synthesize_extractive_answer(query=query, documents=documents)

        if not answer or answer.strip() == "":
            answer = self._synthesize_extractive_answer(query=query, documents=documents)

        # Store in LRU cache
        if use_cache and answer:
            with self._cache_lock:
                self._cache[cache_key] = answer
                if len(self._cache) > self._cache_capacity:
                    self._cache.popitem(last=False)

        return answer

    async def _generate_text(
        self,
        instructions: str,
        prompt: str,
        temperature: float = 0.0,
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
            "max_tokens": 80,
        }

        t0 = time.perf_counter()
        response = await self._client.post(
            url,
            headers=headers,
            json=payload,
            timeout=settings.groq_timeout_seconds,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("Groq response: %.1fms (status=%d)", elapsed_ms, response.status_code)

        if response.status_code == 429:
            raise ExternalServiceError("Groq rate limit exceeded (429).")
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Groq returned non-JSON response.") from exc

        choices = data.get("choices") or [{}]
        content = choices[0].get("message", {}).get("content", "")
        return content.strip()

    @staticmethod
    def _clean_llm_response(text: str) -> str:
        """Removes reasoning tokens (<think>...</think>) if produced by reasoning models."""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return cleaned or text.strip()

    @staticmethod
    def _synthesize_extractive_answer(query: str, documents: list[SearchResultItem]) -> str:
        """
        Sub-millisecond extractive context synthesizer that scores and selects
        the most informative sentences directly from the top retrieved passages.
        """
        if not documents:
            return NO_EVIDENCE_ANSWER

        query_terms = set(re.findall(r"\w+", query.lower()))
        best_sentences = []

        for doc in documents[:2]:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc.text) if len(s.strip()) > 15]
            for s in sentences:
                s_lower = s.lower()
                overlap = sum(1 for term in query_terms if term in s_lower)
                best_sentences.append((overlap, s))

        if best_sentences:
            best_sentences.sort(key=lambda x: x[0], reverse=True)
            top_sents = [s for _, s in best_sentences[:2] if len(s) > 10]
            if top_sents:
                combined = " ".join(top_sents)
                return f"According to the retrieved records: {combined}"

        top_passage = documents[0].text
        return f"According to the retrieved records: {top_passage[:280]}..."

    @staticmethod
    def _default_instructions() -> str:
        return (
            "You are a concise, accurate voice assistant powered by retrieved knowledge. "
            "Answer the user's question directly and briefly based strictly on the provided context. "
            f"If the context lacks sufficient evidence, respond: '{NO_EVIDENCE_ANSWER}' "
            "Do not fabricate facts. Keep answers strictly to 1-2 concise sentences."
        )

    @staticmethod
    def _build_prompt(query: str, documents: list[SearchResultItem]) -> str:
        max_context_chars = min(get_settings().max_context_chars, 4000)
        sections: list[str] = []
        used_chars = 0

        for index, doc in enumerate(documents[:3], start=1):
            section = f"[Source {index}] (ID: {doc.id})\n{doc.text}\n"
            if used_chars + len(section) > max_context_chars:
                remaining = max_context_chars - used_chars
                if remaining > 150:
                    sections.append(section[:remaining])
                break
            sections.append(section)
            used_chars += len(section)

        context = "\n---\n".join(sections)
        return f"User Question: {query}\n\nRetrieved Context:\n{context}\n\nAnswer:"

