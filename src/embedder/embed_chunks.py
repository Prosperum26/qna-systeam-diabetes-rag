"""
Embedding pipeline for processing chunks.

This module:
- Loads chunks from chunked.jsonl
- Embeds text using the Embedder class
- Preserves metadata
- Saves embedded chunks to embedded_chunks.jsonl
- Supports caching, progress tracking, and batch processing
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

from src.embedder.embedder import Embedder


def load_chunks(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load chunks from JSONL file.
    
    Args:
        input_path: Path to chunked.jsonl file
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunk = json.loads(line)
                chunks.append(chunk)
    return chunks


def save_embedded_chunks(
    embedded_chunks: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """
    Save embedded chunks to JSONL file.
    
    Each line is a complete embedded chunk with text, embedding, and metadata.
    
    Args:
        embedded_chunks: List of embedded chunk dictionaries
        output_path: Path to save embedded_chunks.jsonl
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in embedded_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def embed_chunks(
    input_path: Path = Path("data/chunked"),
    output_path: Path = Path("data/embedded"),
    batch_size: int = 32,
    device: str = "cpu",
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    skip_existing: bool = True,
) -> None:
    """
    Main embedding pipeline.
    
    Steps:
    1. Load chunks from chunked.jsonl
    2. Extract text and batch embed
    3. Attach embeddings to chunks
    4. Preserve metadata
    5. Save to embedded_chunks.jsonl
    
    Args:
        input_path: Directory containing chunked.jsonl
        output_path: Directory to save embedded_chunks.jsonl
        batch_size: Number of chunks to embed per batch (default: 32)
        device: Computation device ("cpu" or "cuda", default: "cpu")
        model_name: HuggingFace model name (default: multilingual MiniLM)
        skip_existing: Skip chunks that already have embeddings (default: True)
    """
    # Resolve paths
    input_file = input_path / "chunked.jsonl" if input_path.is_dir() else input_path
    output_dir = output_path if isinstance(output_path, Path) else Path(output_path)
    output_file = output_dir / "embedded_chunks.jsonl"

    print(f"Loading chunks from {input_file}...")
    chunks = load_chunks(input_file)
    print(f"Loaded {len(chunks)} chunks")

    # Initialize embedder
    print(f"Loading embedding model: {model_name}")
    embedder = Embedder(
        model_name=model_name,
        device=device,
        normalize=True,  # Always normalize for cosine similarity
    )
    print("Model loaded successfully")

    # Filter chunks if needed (caching)
    chunks_to_embed = chunks
    if skip_existing:
        chunks_to_embed = [
            chunk for chunk in chunks
            if "embedding" not in chunk or chunk["embedding"] is None
        ]
        skipped = len(chunks) - len(chunks_to_embed)
        if skipped > 0:
            print(f"Skipping {skipped} chunks that already have embeddings")

    if not chunks_to_embed:
        print("All chunks already embedded. Exiting.")
        return

    # Extract texts for embedding
    texts_to_embed = [chunk["text"] for chunk in chunks_to_embed]

    # Embed in batches with progress bar
    print(f"Embedding {len(chunks_to_embed)} chunks in batches of {batch_size}...")
    all_embeddings = []

    for i in tqdm(
        range(0, len(texts_to_embed), batch_size),
        desc="Embedding chunks",
        unit="batch",
    ):
        batch_texts = texts_to_embed[i : i + batch_size]
        batch_embeddings = embedder.embed_batch(batch_texts)
        all_embeddings.extend(batch_embeddings)

    # Attach embeddings to chunks
    # chunks_to_embed references are the same objects as in chunks, so modifications will reflect
    for chunk, embedding in zip(chunks_to_embed, all_embeddings):
        chunk["embedding"] = embedding

    # Use the original chunks list (all modifications reflected)
    embedded_chunks = chunks

    # Save results
    print(f"Saving {len(embedded_chunks)} embedded chunks to {output_file}...")
    save_embedded_chunks(embedded_chunks, output_file)

    print("\n✓ Embedding pipeline completed successfully")
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_file}")
    print(f"  Total chunks: {len(embedded_chunks)}")
    print(f"  Embedding dimension: 384")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Embed chunks using sentence transformers"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/chunked"),
        help="Input directory/file with chunks (default: data/chunked)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/embedded"),
        help="Output directory for embedded chunks (default: data/embedded)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding (default: 32)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use (default: cpu)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="HuggingFace model name",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Do not skip chunks that already have embeddings",
    )

    args = parser.parse_args()

    embed_chunks(
        input_path=args.input,
        output_path=args.output,
        batch_size=args.batch_size,
        device=args.device,
        model_name=args.model,
        skip_existing=not args.no_skip,
    )
