from __future__ import annotations

import pytest
from indexing.chunkers import (
    ChunkingStrategy,
    FixedSizeChunker,
    SentenceAwareChunker,
    SemanticChunker,
    MultiResolutionChunker,
    get_chunker,
)

SAMPLE_TEXT = (
    "Machine learning algorithms build a model based on sample data. "
    "This data is known as training data in order to make predictions. "
    "Deep learning is part of a broader family of machine learning methods. "
    "Neural networks can be supervised, semi-supervised or unsupervised. "
    "Information retrieval systems search for information in a document or corpus."
)


def test_fixed_size_chunker():
    chunker = FixedSizeChunker(token_size=15, overlap=5)
    chunks = chunker.chunk("doc_1", SAMPLE_TEXT, metadata={"source": "test"})
    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_id == "doc_1"
        assert c.strategy == ChunkingStrategy.FIXED.value
        assert c.token_count <= 15
        assert c.metadata["source"] == "test"


def test_sentence_aware_chunker():
    chunker = SentenceAwareChunker(max_tokens=25, min_tokens=10, overlap_sentences=1)
    chunks = chunker.chunk("doc_2", SAMPLE_TEXT)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.document_id == "doc_2"
        assert c.strategy == ChunkingStrategy.SENTENCE.value
        assert len(c.text) > 0


def test_semantic_chunker():
    chunker = SemanticChunker(max_tokens=30, similarity_threshold=0.5)
    chunks = chunker.chunk("doc_3", SAMPLE_TEXT)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.document_id == "doc_3"
        assert c.strategy == ChunkingStrategy.SEMANTIC.value


def test_multi_resolution_chunker():
    chunker = MultiResolutionChunker(small_size=10, medium_size=20, large_size=40)
    chunks = chunker.chunk("doc_4", SAMPLE_TEXT)
    strategies = {c.strategy for c in chunks}
    assert "multi_resolution_large" in strategies
    assert "multi_resolution_medium" in strategies
    assert "multi_resolution_small" in strategies


def test_chunker_factory():
    fixed = get_chunker("fixed", token_size=50)
    assert isinstance(fixed, FixedSizeChunker)

    sentence = get_chunker("sentence_aware")
    assert isinstance(sentence, SentenceAwareChunker)
