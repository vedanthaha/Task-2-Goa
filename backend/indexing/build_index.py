from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from indexing.dataset_loader import MSMARCODataLoader
from indexing.chunkers import get_chunker, ChunkingStrategy
from rag.vector_store import VectorStore
from rag.bm25_search import BM25Index

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger("offline_indexer")


def build_offline_indexes(
    dataset_file: str | None = None,
    strategy: str = "sentence_aware",
    output_dir: str | Path | None = None,
) -> dict[str, int]:
    """
    Offline indexing pipeline:
    1. Ingest & clean MSMARCO-XI passages.
    2. Apply metadata-aware chunking.
    3. Build Dense Vector index.
    4. Build Lexical BM25 index.
    5. Save pre-computed indexes to disk.
    """
    start_time = time.perf_counter()
    out_path = Path(output_dir or BASE_DIR / "data")
    dense_path = out_path / "dense_index"
    bm25_path = out_path / "bm25_index"

    logger.info("=== STARTING OFFLINE MSMARCO-XI INDEXING PIPELINE ===")
    logger.info("Chunking strategy: %s | Output: %s", strategy, out_path)

    # 1. Ingest dataset
    loader = MSMARCODataLoader(data_path=dataset_file)
    documents = loader.load_documents()
    logger.info("Loaded %d documents from MSMARCO-XI dataset.", len(documents))

    # 2. Chunking
    chunker = get_chunker(strategy)
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk(
            document_id=doc.document_id,
            text=doc.text,
            language=doc.language,
            metadata={"title": doc.title, "url": doc.url, **doc.metadata},
        )
        all_chunks.extend(chunks)

    logger.info("Generated %d chunks across %d documents.", len(all_chunks), len(documents))

    chunk_ids = [c.chunk_id for c in all_chunks]
    chunk_texts = [c.text for c in all_chunks]
    chunk_metadatas = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "strategy": c.strategy,
            "language": c.language,
            "token_count": c.token_count,
            "parent_id": c.parent_id,
            **c.metadata,
        }
        for c in all_chunks
    ]

    # 3. Dense Vector Indexing
    logger.info("Building Dense Vector Index...")
    vec_store = VectorStore()
    vec_store.add_documents(ids=chunk_ids, texts=chunk_texts, metadatas=chunk_metadatas)
    vec_store.save(dense_path)
    logger.info("Saved Dense Vector Index to %s", dense_path)

    # 4. BM25 Lexical Indexing
    logger.info("Building BM25 Lexical Index...")
    bm25_idx = BM25Index()
    bm25_idx.add_documents(ids=chunk_ids, texts=chunk_texts, metadatas=chunk_metadatas)
    bm25_idx.save(bm25_path)
    logger.info("Saved BM25 Lexical Index to %s", bm25_path)

    elapsed = round(time.perf_counter() - start_time, 2)
    logger.info("=== OFFLINE INDEXING COMPLETED in %s seconds ===", elapsed)

    return {
        "documents_count": len(documents),
        "chunks_count": len(all_chunks),
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offline Indexer for MSMARCO-XI")
    parser.add_argument("--dataset", type=str, default=None, help="Path to MSMARCO dataset file (json/jsonl)")
    parser.add_argument("--strategy", type=str, default="sentence_aware", choices=["fixed", "sentence_aware", "semantic", "multi_resolution"])
    parser.add_argument("--out", type=str, default=None, help="Output directory for pre-computed indexes")
    args = parser.parse_args()

    build_offline_indexes(dataset_file=args.dataset, strategy=args.strategy, output_dir=args.out)
