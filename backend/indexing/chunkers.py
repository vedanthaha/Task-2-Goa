from __future__ import annotations

import re
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChunkingStrategy(str, Enum):
    FIXED = "fixed"
    SENTENCE = "sentence_aware"
    SEMANTIC = "semantic"
    MULTI_RESOLUTION = "multi_resolution"


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    token_count: int
    strategy: str
    parent_id: str | None = None
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


def simple_tokenize(text: str) -> list[str]:
    """Tokenize text into whitespace-delimited words / tokens."""
    return re.findall(r"\S+", text)


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences using regex boundary detection."""
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in raw_sentences if s.strip()]


class BaseChunker(ABC):
    @abstractmethod
    def chunk(
        self,
        document_id: str,
        text: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        pass

    @staticmethod
    def _generate_chunk_id(document_id: str, strategy: str, index: int, text: str) -> str:
        digest = hashlib.sha256(f"{document_id}:{strategy}:{index}:{text}".encode("utf-8")).hexdigest()[:12]
        return f"{document_id}_{strategy}_{index}_{digest}"


class FixedSizeChunker(BaseChunker):
    """Fixed-size chunker with configurable token size and overlap."""

    def __init__(self, token_size: int = 150, overlap: int = 30) -> None:
        if overlap >= token_size:
            overlap = max(0, int(token_size * 0.2))
        self.token_size = token_size
        self.overlap = overlap

    def chunk(
        self,
        document_id: str,
        text: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        tokens = simple_tokenize(text)
        if not tokens:
            return []

        chunks: list[Chunk] = []
        start = 0
        idx = 0
        step = max(1, self.token_size - self.overlap)

        while start < len(tokens):
            end = min(start + self.token_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)

            chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.FIXED.value, idx, chunk_text)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    token_count=len(chunk_tokens),
                    strategy=ChunkingStrategy.FIXED.value,
                    language=language,
                    metadata=dict(metadata or {}),
                )
            )
            idx += 1
            if end >= len(tokens):
                break
            start += step

        return chunks


class SentenceAwareChunker(BaseChunker):
    """Sentence-aware chunker that accumulates complete sentences up to max_tokens."""

    def __init__(self, max_tokens: int = 200, min_tokens: int = 40, overlap_sentences: int = 1) -> None:
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_sentences = overlap_sentences

    def chunk(
        self,
        document_id: str,
        text: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        sentences = split_into_sentences(text)
        if not sentences:
            return []

        chunks: list[Chunk] = []
        current_sentences: list[str] = []
        current_token_count = 0
        idx = 0

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_tokens = len(simple_tokenize(sentence))

            if current_token_count + sentence_tokens > self.max_tokens and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.SENTENCE.value, idx, chunk_text)
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        text=chunk_text,
                        token_count=current_token_count,
                        strategy=ChunkingStrategy.SENTENCE.value,
                        language=language,
                        metadata=dict(metadata or {}),
                    )
                )
                idx += 1

                overlap = current_sentences[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                current_sentences = list(overlap)
                current_token_count = sum(len(simple_tokenize(s)) for s in current_sentences)

            current_sentences.append(sentence)
            current_token_count += sentence_tokens
            i += 1

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.SENTENCE.value, idx, chunk_text)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    token_count=current_token_count,
                    strategy=ChunkingStrategy.SENTENCE.value,
                    language=language,
                    metadata=dict(metadata or {}),
                )
            )

        return chunks


class SemanticChunker(BaseChunker):
    """Semantic chunker using lexical similarity / topic boundary heuristics across sentence groups."""

    def __init__(self, max_tokens: int = 250, similarity_threshold: float = 0.6) -> None:
        self.max_tokens = max_tokens
        self.similarity_threshold = similarity_threshold

    def chunk(
        self,
        document_id: str,
        text: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        sentences = split_into_sentences(text)
        if not sentences:
            return []

        if len(sentences) == 1:
            tokens = simple_tokenize(sentences[0])
            chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.SEMANTIC.value, 0, sentences[0])
            return [
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=sentences[0],
                    token_count=len(tokens),
                    strategy=ChunkingStrategy.SEMANTIC.value,
                    language=language,
                    metadata=dict(metadata or {}),
                )
            ]

        chunks: list[Chunk] = []
        current_group: list[str] = [sentences[0]]
        current_tokens = len(simple_tokenize(sentences[0]))
        idx = 0

        for i in range(1, len(sentences)):
            prev_sentence = sentences[i - 1]
            curr_sentence = sentences[i]
            curr_tokens = len(simple_tokenize(curr_sentence))

            prev_words = set(w.lower() for w in simple_tokenize(prev_sentence) if len(w) > 2)
            curr_words = set(w.lower() for w in simple_tokenize(curr_sentence) if len(w) > 2)
            
            similarity = len(prev_words & curr_words) / max(1, len(prev_words | curr_words))

            is_boundary = (similarity < self.similarity_threshold and current_tokens > 40) or (
                current_tokens + curr_tokens > self.max_tokens
            )

            if is_boundary and current_group:
                chunk_text = " ".join(current_group)
                chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.SEMANTIC.value, idx, chunk_text)
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        text=chunk_text,
                        token_count=current_tokens,
                        strategy=ChunkingStrategy.SEMANTIC.value,
                        language=language,
                        metadata=dict(metadata or {}),
                    )
                )
                idx += 1
                current_group = [curr_sentence]
                current_tokens = curr_tokens
            else:
                current_group.append(curr_sentence)
                current_tokens += curr_tokens

        if current_group:
            chunk_text = " ".join(current_group)
            chunk_id = self._generate_chunk_id(document_id, ChunkingStrategy.SEMANTIC.value, idx, chunk_text)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    token_count=current_tokens,
                    strategy=ChunkingStrategy.SEMANTIC.value,
                    language=language,
                    metadata=dict(metadata or {}),
                )
            )

        return chunks


class MultiResolutionChunker(BaseChunker):
    """Multi-resolution hierarchical chunker maintaining small, medium, and large parent-child chunks."""

    def __init__(
        self,
        small_size: int = 80,
        medium_size: int = 200,
        large_size: int = 400,
    ) -> None:
        self.small_chunker = FixedSizeChunker(token_size=small_size, overlap=max(0, int(small_size * 0.15)))
        self.medium_chunker = FixedSizeChunker(token_size=medium_size, overlap=max(0, int(medium_size * 0.15)))
        self.large_chunker = FixedSizeChunker(token_size=large_size, overlap=max(0, int(large_size * 0.15)))

    def chunk(
        self,
        document_id: str,
        text: str,
        language: str = "en",
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        large_chunks = self.large_chunker.chunk(document_id, text, language, metadata)
        all_chunks: list[Chunk] = []

        for l_idx, l_chunk in enumerate(large_chunks):
            l_chunk.strategy = "multi_resolution_large"
            l_chunk.metadata["resolution"] = "large"
            all_chunks.append(l_chunk)

            medium_chunks = self.medium_chunker.chunk(f"{l_chunk.chunk_id}_m", l_chunk.text, language, metadata)
            for m_chunk in medium_chunks:
                m_chunk.parent_id = l_chunk.chunk_id
                m_chunk.strategy = "multi_resolution_medium"
                m_chunk.metadata["resolution"] = "medium"
                all_chunks.append(m_chunk)

                small_chunks = self.small_chunker.chunk(f"{m_chunk.chunk_id}_s", m_chunk.text, language, metadata)
                for s_chunk in small_chunks:
                    s_chunk.parent_id = m_chunk.chunk_id
                    s_chunk.strategy = "multi_resolution_small"
                    s_chunk.metadata["resolution"] = "small"
                    all_chunks.append(s_chunk)

        return all_chunks


def get_chunker(strategy: ChunkingStrategy | str, **kwargs: Any) -> BaseChunker:
    """Factory function for pluggable chunking strategies."""
    strat = ChunkingStrategy(strategy) if isinstance(strategy, str) else strategy
    if strat == ChunkingStrategy.FIXED:
        return FixedSizeChunker(**kwargs)
    elif strat == ChunkingStrategy.SENTENCE:
        return SentenceAwareChunker(**kwargs)
    elif strat == ChunkingStrategy.SEMANTIC:
        return SemanticChunker(**kwargs)
    elif strat == ChunkingStrategy.MULTI_RESOLUTION:
        return MultiResolutionChunker(**kwargs)
    raise ValueError(f"Unknown chunking strategy: {strategy}")
