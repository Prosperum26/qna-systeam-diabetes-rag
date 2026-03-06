"""
Test module for the VectorStore implementation.

Uses pre-embedded chunks from data/embedded/embedded_chunks.jsonl.
Does not re-embed text; only tests vector store behavior.

Run directly: python tests/test_vectorstore.py
Or with pytest: pytest tests/test_vectorstore.py -v
"""

import gc
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Project root for imports and data paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.vectorstore.base import EXPECTED_EMBEDDING_DIM
    from src.vectorstore.chroma_store import ChromaVectorStore
    _VECTORSTORE_AVAILABLE = True
    _IMPORT_ERROR = None
except ImportError as e:
    _VECTORSTORE_AVAILABLE = False
    _IMPORT_ERROR = e
    EXPECTED_EMBEDDING_DIM = 384  # fallback for load_embedded_chunks/validate_chunks

# Path to embedded chunks (384-dim, paraphrase-multilingual-MiniLM-L12-v2)
EMBEDDED_CHUNKS_PATH = PROJECT_ROOT / "data" / "embedded" / "embedded_chunks.jsonl"


def load_embedded_chunks(path: Path) -> list[dict]:
    """
    Read the JSONL file and return a list of chunk dicts.

    Each line must have: chunk_id, doc_id, text, embedding, metadata.
    """
    if not path.exists():
        raise FileNotFoundError(f"Embedded chunks file not found: {path}")

    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}") from e
    return chunks


def validate_chunks(chunks: list[dict], embedding_dim: int = EXPECTED_EMBEDDING_DIM) -> None:
    """Ensure embeddings are 384-dim, no empty documents, metadata exists."""
    for i, c in enumerate(chunks):
        if "embedding" not in c:
            raise ValueError(f"Chunk {i} missing 'embedding'")
        if len(c["embedding"]) != embedding_dim:
            raise ValueError(
                f"Chunk {i}: expected embedding dim {embedding_dim}, got {len(c['embedding'])}"
            )
        if not (c.get("text") or "").strip():
            raise ValueError(f"Chunk {i} has empty document text")
        if "metadata" not in c or not isinstance(c["metadata"], dict):
            raise ValueError(f"Chunk {i} missing or invalid 'metadata'")


@unittest.skipIf(not _VECTORSTORE_AVAILABLE, f"VectorStore backend not available: {_IMPORT_ERROR}")
class TestVectorStore(unittest.TestCase):
    """Test VectorStore load -> insert -> search -> persist -> reload -> search."""

    def test_vectorstore_flow(self) -> None:
        # 1. Load embedded chunks
        chunks = load_embedded_chunks(EMBEDDED_CHUNKS_PATH)
        self.assertGreater(len(chunks), 0, "JSONL should contain at least one chunk")
        validate_chunks(chunks)
        print(f"Loaded {len(chunks)} chunks")

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        embeddings = [c["embedding"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        with tempfile.TemporaryDirectory(prefix="vectorstore_test_") as tmpdir:
            persist_path = Path(tmpdir)

            # 2. Create vector store (Chroma only; no FAISS dependency)
            store = ChromaVectorStore(persist_path=persist_path)
            print("Vector store created")

            # 3. Insert documents
            store.add_documents(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
            print(f"Inserted {len(ids)} documents")

            # 4. Similarity search using one chunk's embedding as query
            query_embedding = chunks[0]["embedding"]
            top_k = 3
            results = store.similarity_search(query_embedding, top_k=top_k)

            self.assertGreater(len(results), 0, "Similarity search should return at least one result")
            for r in results:
                self.assertIn("chunk_id", r, "Result must contain chunk_id")
                self.assertIn("text", r, "Result must contain text")
                self.assertIn("score", r, "Result must contain score")
                self.assertIn("metadata", r, "Result must contain metadata")
                self.assertIsInstance(r["score"], (int, float), "Score must be numeric")
                self.assertIsInstance(r["metadata"], dict, "metadata must be a dict")

            # Scores sorted descending (higher = more similar)
            scores = [r["score"] for r in results]
            self.assertEqual(scores, sorted(scores, reverse=True), "Results must be sorted by score descending")
            print(f"Top result score: {results[0]['score']}")

            # 5. Persist
            store.persist()
            print("Vector store persisted")

            # 6. Reload into a new store instance
            store2 = ChromaVectorStore(persist_path=persist_path)
            store2.load(path=persist_path)
            print("Vector store reloaded")

            # 7. Search again
            results2 = store2.similarity_search(query_embedding, top_k=top_k)
            self.assertGreater(len(results2), 0, "Search after reload should return results")
            print("Search successful")

            # 8. Clean up vectorstore instances to release file handles
            del store
            del store2
            gc.collect()
            
            # 9. Short delay to allow Windows to release file locks
            time.sleep(0.3)


if __name__ == "__main__":
    unittest.main()
