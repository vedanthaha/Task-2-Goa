from __future__ import annotations

import pytest
from rag.embeddings import FastDenseEmbedder
from rag.vector_store import VectorStore
from rag.bm25_search import BM25Index
from rag.hybrid_retriever import HybridRetriever


def test_dense_embedder():
    embedder = FastDenseEmbedder(dimension=64)
    v1 = embedder.embed_text("machine learning neural network")
    v2 = embedder.embed_text("deep neural network artificial intelligence")
    v3 = embedder.embed_text("solar panel renewable energy")

    assert v1.shape == (64,)
    # Semantic similarity between AI topics should be higher than AI vs Solar
    sim_12 = float(v1 @ v2)
    sim_13 = float(v1 @ v3)
    assert sim_12 > sim_13


def test_vector_store():
    store = VectorStore(embedder=FastDenseEmbedder(dimension=64))
    store.add_documents(
        ids=["d1", "d2"],
        texts=["Solar energy generates green electricity", "Machine learning creates neural networks"],
        metadatas=[{"topic": "energy"}, {"topic": "ai"}],
    )
    results = store.search("renewable solar power", top_k=2)
    assert len(results) == 2
    assert results[0].id == "d1"

    # Test filtering
    filtered = store.search("power", top_k=2, filters={"topic": "ai"})
    assert len(filtered) == 1
    assert filtered[0].id == "d2"


def test_bm25_search():
    bm25 = BM25Index()
    bm25.add_documents(
        ids=["b1", "b2"],
        texts=["The quick brown fox jumps over the lazy dog", "Artificial intelligence and machine learning models"],
    )
    results = bm25.search("quick fox", top_k=2)
    assert len(results) >= 1
    assert results[0].id == "b1"


@pytest.mark.asyncio
async def test_hybrid_retriever_rrf():
    vec = VectorStore()
    bm25 = BM25Index()

    ids = ["doc_ai", "doc_solar", "doc_speech"]
    texts = [
        "Machine learning models with deep neural network training",
        "Solar photovoltaic panels generate renewable solar energy",
        "Speech to text voice recognition transcript conversion",
    ]

    vec.add_documents(ids, texts)
    bm25.add_documents(ids, texts)

    hybrid = HybridRetriever(vector_store=vec, bm25_index=bm25, rrf_k=60)
    results = await hybrid.search("speech to text voice", top_k=3)

    assert len(results) == 3
    assert results[0].id == "doc_speech"
    assert results[0].fused_score > 0
    assert results[0].dense_rank is not None
    assert results[0].bm25_rank is not None
