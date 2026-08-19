from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from functools import lru_cache
import numpy as np


class EmbeddingModel(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> np.ndarray:
        pass


class FastDenseEmbedder(EmbeddingModel):
    """
    Ultra-low-latency deterministic dense embedding model with sub-word n-grams,
    feature hashing, L2-normalization, and thread-safe LRU caching.
    """

    def __init__(self, dimension: int = 128, cache_size: int = 4096) -> None:
        self.dimension = dimension
        self.cache_size = cache_size
        self._cached_embed_text = lru_cache(maxsize=cache_size)(self._raw_embed_text)

    def _raw_embed_text(self, text: str) -> tuple[float, ...]:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = re.findall(r"\w+", text.lower())
        if not words:
            return tuple(vec)

        for word in words:
            h_word = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h_word % self.dimension
            sign = 1.0 if ((h_word >> 8) & 1) == 1 else -1.0
            vec[idx] += sign * 1.5

            if len(word) >= 3:
                for j in range(len(word) - 2):
                    ngram = word[j : j + 3]
                    h_ng = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    ng_idx = h_ng % self.dimension
                    ng_sign = 1.0 if ((h_ng >> 8) & 1) == 1 else -1.0
                    vec[ng_idx] += ng_sign * 0.5

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec /= norm
        return tuple(vec)

    def embed_text(self, text: str) -> np.ndarray:
        return np.array(self._cached_embed_text(text), dtype=np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)
        return np.stack([self.embed_text(t) for t in texts], axis=0)

    def clear_cache(self) -> None:
        self._cached_embed_text.cache_clear()
