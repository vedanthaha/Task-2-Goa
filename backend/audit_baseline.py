import asyncio
import json
import logging
from pathlib import Path

from app import app
from models.schemas import QueryRequest
from rag.orchestrator import RAGOrchestrator
from services.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_audit():
    print("================ DATASET AUDIT ================")
    data_dir = Path("data")
    
    # 1. Vector Store check
    try:
        with open(data_dir / "dense_index" / "docs.json", "r", encoding="utf-8") as f:
            v_data = json.load(f)
            print(f"Vector Index Docs: {len(v_data['doc_ids'])}")
    except Exception as e:
        print(f"Failed to read vector index: {e}")

    # 2. BM25 Index check
    try:
        with open(data_dir / "bm25_index" / "bm25_data.json", "r", encoding="utf-8") as f:
            b_data = json.load(f)
            print(f"BM25 Index Docs: {len(b_data['doc_ids'])}")
    except Exception as e:
        print(f"Failed to read BM25 index: {e}")

    print("\n================ QUERY AUDIT ================")
    # Initialize orchestrator
    orchestrator = RAGOrchestrator()
    
    queries = [
        # 1. Existing question that works (assuming this is one of the ~7 patterns)
        "What is the capital of France?",
        # 2. Paraphrase of a working question
        "Can you tell me the capital city of France?",
        # 3. Question about a different topic that should exist in the dataset
        "Who was Albert Einstein?",
        # 4. Longer natural-language question
        "I was wondering if you could explain in detail how quantum computing actually works?",
        # 5. Unsupported question
        "What is the meaning of life?",
    ]
    
    for q in queries:
        print(f"\n--- QUERY: '{q}' ---")
        try:
            # We bypass the API and call orchestrator directly for deeper inspection
            response = await orchestrator.execute_query(query=q, use_cache=False)
            
            print(f"Answer: {response.answer}")
            print(f"Latency: {response.latency.total_pipeline_ms}ms")
            
            # Print guardrails reason if available
            if not response.guardrails.is_on_topic:
                print(f"On Topic Flag Reasons: {response.guardrails.flag_reasons}")

            print(f"Citations: {len(response.citations)}")
            for c in response.citations:
                safe_text = c.text[:60].encode("ascii", "replace").decode("ascii")
                print(f"  - [{c.id}] (Score: {c.score}): {safe_text}...")
            
            await asyncio.sleep(3) # Avoid Groq rate limits
                
        except Exception as e:
            print(f"Error processing query: {e}")

if __name__ == "__main__":
    asyncio.run(run_audit())
