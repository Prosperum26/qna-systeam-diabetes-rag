"""
Prepare embedded chunks for semantic search test.

Reads all *_chunks.jsonl (or *.jsonl) from data/chunked/,
embeds each chunk's text with Embedder, and writes
data/embedded/embedded_chunks.jsonl so tests/test_semantic_search.py can run.

Usage (from project root):
  python tests/embed_chunks_for_test.py [--device cpu]
"""

import json
import sys
from pathlib import Path

# Project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.embedder.embedder import Embedder


CHUNKED_DIR = project_root / "data" / "chunked"
EMBEDDED_DIR = project_root / "data" / "embedded"
OUTPUT_FILE = EMBEDDED_DIR / "embedded_chunks.jsonl"

BATCH_SIZE = 32


def load_all_chunks(chunked_dir: Path) -> list[dict]:
    """Load chunks from every JSONL in chunked_dir."""
    chunks: list[dict] = []
    for path in sorted(chunked_dir.glob("*.jsonl")):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
    return chunks


def ensure_metadata(chunk: dict) -> dict:
    """Ensure chunk has 'metadata' for test_semantic_search display."""
    out = dict(chunk)
    if "metadata" not in out or not out["metadata"]:
        out["metadata"] = {
            "title": chunk.get("title", ""),
            "heading": chunk.get("heading", ""),
            "position": chunk.get("position", 0),
        }
    return out


def main(device: str = "cpu") -> None:
    if not CHUNKED_DIR.is_dir():
        print(f"Chunked dir not found: {CHUNKED_DIR}")
        sys.exit(1)

    chunks = load_all_chunks(CHUNKED_DIR)
    if not chunks:
        print(f"No chunks found under {CHUNKED_DIR}")
        sys.exit(1)

    print(f"Loaded {len(chunks)} chunks from {CHUNKED_DIR}")

    embedder = Embedder(device=device)
    texts = [c["text"] for c in chunks]
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        emb = embedder.embed_batch(batch)
        all_embeddings.extend(emb)

    for chunk, embedding in zip(chunks, all_embeddings):
        chunk["embedding"] = embedding

    EMBEDDED_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for chunk in chunks:
            out = ensure_metadata(chunk)
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"Saved {len(chunks)} embedded chunks to {OUTPUT_FILE}")
    print("Run: python tests/test_semantic_search.py")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Embed chunks for semantic search test")
    p.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    args = p.parse_args()
    main(device=args.device)
