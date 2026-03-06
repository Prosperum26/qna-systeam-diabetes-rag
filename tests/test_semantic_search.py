"""
Semantic Search Test

Verify that embeddings are semantically meaningful.

This test:
- Loads embedded chunks from JSONL file
- Embeds a Vietnamese query
- Computes cosine similarity with chunk embeddings
- Returns and displays top 3 most similar chunks
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embedder.embedder import Embedder


def load_embedded_chunks(file_path: Path) -> List[Dict]:
    """
    Load embedded chunks from JSONL file.
    
    Args:
        file_path: Path to embedded_chunks.jsonl
        
    Returns:
        List of chunk dictionaries with embeddings
    """
    chunks = []
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    chunk = json.loads(line)
                    chunks.append(chunk)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}")
                    continue
    
    return chunks


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Formula: cos(θ) = (a · b) / (||a|| * ||b||)
    
    Args:
        vec_a: First vector
        vec_b: Second vector
        
    Returns:
        Cosine similarity score (-1 to 1)
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def search_similar_chunks(
    query: str,
    chunks: List[Dict],
    embedder: Embedder,
    top_k: int = 3,
) -> List[Tuple[Dict, float]]:
    """
    Find top-k chunks most similar to query.
    
    Args:
        query: Search query text
        chunks: List of chunk dictionaries with embeddings
        embedder: Embedder instance
        top_k: Number of top results to return
        
    Returns:
        List of (chunk, similarity_score) tuples
    """
    # Embed query
    query_embedding = np.array(embedder.embed(query))
    
    # Compute similarities with all chunks
    similarities = []
    for chunk in chunks:
        if "embedding" not in chunk:
            continue
        
        chunk_embedding = np.array(chunk["embedding"])
        sim = cosine_similarity(query_embedding, chunk_embedding)
        similarities.append((chunk, sim))
    
    # Sort by similarity (descending) and return top-k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def format_chunk_text(text: str, max_length: int = 200) -> str:
    """
    Format chunk text for display, truncating if necessary.
    
    Args:
        text: Full text
        max_length: Maximum display length
        
    Returns:
        Formatted text
    """
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def test_semantic_search():
    """Test semantic search with embeddings."""
    
    print("=" * 70)
    print("TEST: Semantic Search with Embeddings")
    print("=" * 70)
    
    embedded_file = Path(project_root) / "data" / "embedded" / "embedded_chunks.jsonl"
    query = "Cách tính lượng đường trong thức ăn?"
    
    try:
        # Load embedded chunks
        print(f"\nLoading embedded chunks from: {embedded_file}")
        if not embedded_file.exists():
            print(f"✗ File not found: {embedded_file}")
            print("\nCreate embeddings first using:")
            print("  python -m src.embedder.embed_chunks")
            return False
        
        chunks = load_embedded_chunks(embedded_file)
        print(f"✓ Loaded {len(chunks)} chunks")
        
        if not chunks:
            print("✗ No chunks found in file")
            return False
        
        # Initialize embedder
        print(f"\nInitializing Embedder...")
        embedder = Embedder(device="cpu")
        print("✓ Embedder initialized")
        
        # Semantic search
        print(f"\n--- Semantic Search ---")
        print(f"Query: {query}\n")
        
        results = search_similar_chunks(query, chunks, embedder, top_k=3)
        
        if not results:
            print("✗ No results found")
            return False
        
        print(f"✓ Found {len(results)} similar chunks\n")
        
        # Display results
        for rank, (chunk, similarity) in enumerate(results, 1):
            print(f"{'─' * 70}")
            print(f"Top {rank}")
            print(f"Similarity Score: {similarity:.4f}")
            
            # Display metadata
            metadata = chunk.get("metadata", {})
            if metadata:
                if "title" in metadata:
                    print(f"Title: {metadata['title']}")
                if "heading" in metadata:
                    print(f"Heading: {metadata['heading']}")
                if "position" in metadata:
                    print(f"Position: {metadata['position']}")
            
            # Display text (truncated)
            text = chunk.get("text", "")
            formatted_text = format_chunk_text(text, max_length=200)
            print(f"Text: {formatted_text}")
        
        print(f"{'─' * 70}\n")
        
        # Validation
        print("--- Validation ---")
        assert len(results) >= 1, "Should have at least 1 result"
        print("✓ Results returned")
        
        assert all(isinstance(score, float) for _, score in results), "Scores should be floats"
        print("✓ All scores are floats")
        
        assert all(-1.0 <= score <= 1.0 for _, score in results), "Scores should be in [-1, 1]"
        print("✓ All scores are in valid range [-1, 1]")
        
        # Check that results are sorted by similarity
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by similarity"
        print("✓ Results are sorted by similarity")
        
        print(f"\n{'=' * 70}")
        print("✓ Semantic search test PASSED")
        print(f"{'=' * 70}\n")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n✗ File error: {e}")
        print("\nTo fix this:")
        print("1. Make sure data/chunked/chunked.jsonl exists")
        print("2. Run: python -m src.embedder.embed_chunks")
        print(f"{'=' * 70}\n")
        return False
        
    except Exception as e:
        print(f"\n✗ Test FAILED with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'=' * 70}\n")
        return False


def test_multiple_queries():
    """Test semantic search with multiple queries."""
    
    print("=" * 70)
    print("TEST: Multiple Semantic Search Queries")
    print("=" * 70)
    
    embedded_file = Path(project_root) / "data" / "embedded" / "embedded_chunks.jsonl"
    
    test_queries = [
        "Sữa chua có ăn được cho người tiểu đường?",
        "Đột biến gen có gây bệnh tiểu đường?",
        "Cách tính lượng đường trong đồ ăn?",
    ]
    
    try:
        # Load chunks
        if not embedded_file.exists():
            print(f"✗ File not found: {embedded_file}")
            return False
        
        chunks = load_embedded_chunks(embedded_file)
        if not chunks:
            print("✗ No chunks found")
            return False
        
        # Initialize embedder
        embedder = Embedder(device="cpu")
        
        # Test each query
        print(f"\nTesting {len(test_queries)} queries...\n")
        
        for i, query in enumerate(test_queries, 1):
            print(f"Query {i}: {query}")
            results = search_similar_chunks(query, chunks, embedder, top_k=1)
            
            if results:
                top_chunk, top_score = results[0]
                text_preview = format_chunk_text(top_chunk.get("text", ""), max_length=100)
                print(f"  → Top match (score: {top_score:.4f})")
                print(f"  → Text: {text_preview}\n")
            else:
                print("  → No matches found\n")
        
        print(f"{'=' * 70}")
        print("✓ Multiple queries test PASSED")
        print(f"{'=' * 70}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        print(f"{'=' * 70}\n")
        return False


if __name__ == "__main__":
    print("\n")
    result1 = test_semantic_search()
    result2 = test_multiple_queries()
    
    if result1 and result2:
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70 + "\n")
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("⚠ SOME TESTS NEED EMBEDDED DATA")
        print("=" * 70)
        print("\nTo get started:")
        print("1. Ensure data/chunked/chunked.jsonl exists")
        print("2. Run: python -m src.embedder.embed_chunks")
        print("\n" + "=" * 70 + "\n")
        sys.exit(1)
