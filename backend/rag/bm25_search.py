from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import numpy as np
from rank_bm25 import BM25Okapi


@dataclass
class BM25SearchResult:
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


def bm25_tokenize(text: str) -> list[str]:
    """Tokenize words and alphanumeric terms for BM25 indexing."""
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]


class BM25Index:
    """Lexical BM25 retrieval engine powered by Okapi BM25 with term frequency smoothing."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.doc_ids: list[str] = []
        self.texts: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.tokenized_corpus: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        if not ids or not texts:
            return 0

        metas = metadatas or [{} for _ in ids]
        for doc_id, text, meta in zip(ids, texts, metas):
            tokens = bm25_tokenize(text)
            self.doc_ids.append(doc_id)
            self.texts.append(text)
            self.metadatas.append(meta)
            self.tokenized_corpus.append(tokens)

        # Set epsilon=0.25 to prevent negative or zero IDF for small test corpora
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b, epsilon=0.25)
        return len(ids)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[BM25SearchResult]:
        if self.bm25 is None or not self.doc_ids:
            return []

        tokens = bm25_tokenize(query)
        if not tokens:
            return []

        raw_scores = np.array(self.bm25.get_scores(tokens), dtype=np.float32)

        # Fallback term frequency count if all Okapi IDF scores are zero (small corpus)
        if np.all(raw_scores <= 0):
            for i, doc_tokens in enumerate(self.tokenized_corpus):
                doc_set = set(doc_tokens)
                raw_scores[i] = float(sum(1 for t in tokens if t in doc_set))

        max_score = float(np.max(raw_scores)) if len(raw_scores) > 0 and np.max(raw_scores) > 0 else 1.0

        # Filter and rank
        valid_indices = []
        for i, meta in enumerate(self.metadatas):
            if filters:
                match = all(meta.get(k) == v for k, v in filters.items())
                if not match:
                    continue
            valid_indices.append(i)

        if not valid_indices:
            return []

        scored_candidates = []
        for idx in valid_indices:
            score = float(raw_scores[idx])
            if score > 0:
                normalized_score = min(1.0, score / max_score)
                scored_candidates.append((idx, normalized_score))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:top_k]

        results = []
        for idx, norm_score in top_candidates:
            results.append(
                BM25SearchResult(
                    id=self.doc_ids[idx],
                    text=self.texts[idx],
                    score=norm_score,
                    metadata=self.metadatas[idx],
                )
            )

        return results

    def save(self, directory: Path | str) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "bm25_data.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "doc_ids": self.doc_ids,
                    "texts": self.texts,
                    "metadatas": self.metadatas,
                    "k1": self.k1,
                    "b": self.b,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, directory: Path | str) -> bool:
        path = Path(directory)
        file = path / "bm25_data.json"
        if not file.exists():
            return False

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.doc_ids = data["doc_ids"]
            self.texts = data["texts"]
            self.metadatas = data["metadatas"]
            self.k1 = data.get("k1", 1.5)
            self.b = data.get("b", 0.75)
            self.tokenized_corpus = [bm25_tokenize(t) for t in self.texts]
            if self.tokenized_corpus:
                self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b, epsilon=0.25)
        return True
