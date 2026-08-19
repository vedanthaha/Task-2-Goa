from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import numpy as np

from .embeddings import EmbeddingModel, FastDenseEmbedder


@dataclass
class VectorSearchResult:
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """In-memory cosine vector store with batch indexing and metadata filtering."""

    def __init__(self, embedder: EmbeddingModel | None = None) -> None:
        self.embedder = embedder or FastDenseEmbedder()
        self.doc_ids: list[str] = []
        self.texts: list[str] = []
        self.metadatas: list[dict[str, Any]] = []
        self.vectors: np.ndarray | None = None

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        vectors: np.ndarray | None = None,
    ) -> int:
        if not ids or not texts:
            return 0

        metas = metadatas or [{} for _ in ids]
        if vectors is None:
            vectors = self.embedder.embed_batch(texts)

        if self.vectors is None or len(self.doc_ids) == 0:
            self.vectors = vectors
            self.doc_ids = list(ids)
            self.texts = list(texts)
            self.metadatas = list(metas)
        else:
            self.vectors = np.vstack([self.vectors, vectors])
            self.doc_ids.extend(ids)
            self.texts.extend(texts)
            self.metadatas.extend(metas)

        return len(ids)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        if self.vectors is None or len(self.doc_ids) == 0:
            return []

        query_vec = self.embedder.embed_text(query)
        # Cosine similarity (both query_vec and database vectors are L2-normalized)
        scores = np.dot(self.vectors, query_vec)

        # Apply metadata filters if supplied
        valid_indices = []
        for i, meta in enumerate(self.metadatas):
            if filters:
                match = all(meta.get(k) == v for k, v in filters.items())
                if not match:
                    continue
            valid_indices.append(i)

        if not valid_indices:
            return []

        valid_scores = scores[valid_indices]
        top_sub_indices = np.argsort(valid_scores)[::-1][:top_k]

        results = []
        for sub_idx in top_sub_indices:
            orig_idx = valid_indices[sub_idx]
            results.append(
                VectorSearchResult(
                    id=self.doc_ids[orig_idx],
                    text=self.texts[orig_idx],
                    score=float(scores[orig_idx]),
                    metadata=self.metadatas[orig_idx],
                )
            )

        return results

    def save(self, directory: Path | str) -> None:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        if self.vectors is not None:
            np.save(path / "vectors.npy", self.vectors)
        with open(path / "docs.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "doc_ids": self.doc_ids,
                    "texts": self.texts,
                    "metadatas": self.metadatas,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, directory: Path | str) -> bool:
        path = Path(directory)
        vec_file = path / "vectors.npy"
        doc_file = path / "docs.json"
        if not vec_file.exists() or not doc_file.exists():
            return False

        self.vectors = np.load(vec_file)
        with open(doc_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.doc_ids = data["doc_ids"]
            self.texts = data["texts"]
            self.metadatas = data["metadatas"]
        return True
