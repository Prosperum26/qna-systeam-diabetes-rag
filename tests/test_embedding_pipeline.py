"""
Embedding Pipeline Test

Verify that the embedding model is working correctly.

This test:
- Instantiates the Embedder
- Embeds a Vietnamese test query
- Validates that the embedding is 384-dimensional
- Prints debugging information
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embedder.embedder import Embedder


def test_embedding_pipeline():
    """Test basic embedding functionality."""
    
    print("=" * 60)
    print("TEST: Embedding Pipeline")
    print("=" * 60)
    
    # Test query in Vietnamese
    query = "Cách tính lượng đường trong thức ăn?"
    print(f"\nTest Query: {query}")
    
    try:
        # Initialize embedder
        print("\nInitializing Embedder...")
        embedder = Embedder(device="cpu")
        print("✓ Embedder initialized successfully")
        
        # Embed the query
        print(f"\nEmbedding query...")
        vector = embedder.embed(query)
        print("✓ Query embedded successfully")
        
        # Validate embedding
        print(f"\n--- Embedding Details ---")
        print(f"Vector length: {len(vector)}")
        print(f"First 5 values: {vector[:5]}")
        print(f"Last 5 values: {vector[-5:]}")
        print(f"Min value: {min(vector):.6f}")
        print(f"Max value: {max(vector):.6f}")
        
        # Check normalization (should be close to 1.0)
        norm = sum(x**2 for x in vector) ** 0.5
        print(f"L2 norm: {norm:.6f} (should be ~1.0)")
        
        # Assertions
        print(f"\n--- Assertions ---")
        
        # Check vector length
        assert len(vector) == 384, f"Expected 384 dimensions, got {len(vector)}"
        print("✓ Vector has 384 dimensions")
        
        # Check vector is not zero
        assert any(x != 0 for x in vector), "Embedding vector is all zeros"
        print("✓ Vector contains non-zero values")
        
        # Check normalization
        assert abs(norm - 1.0) < 1e-5, f"Vector should be normalized to 1.0, got {norm}"
        print("✓ Vector is properly L2 normalized")
        
        # Check all values are floats
        assert all(isinstance(x, float) for x in vector), "Not all values are floats"
        print("✓ All values are floats")
        
        print(f"\n{'=' * 60}")
        print("✓ Embedding test PASSED")
        print(f"{'=' * 60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        print(f"{'=' * 60}\n")
        return False


def test_batch_embedding():
    """Test batch embedding functionality."""
    
    print("=" * 60)
    print("TEST: Batch Embedding")
    print("=" * 60)
    
    test_queries = [
        "Sữa chua có ăn được cho người tiểu đường?",
        "Đột biến gen có gây bệnh tiểu đường?",
        "Cách tính lượng đường trong đồ ăn?",
    ]
    
    try:
        # Initialize embedder
        print("\nInitializing Embedder...")
        embedder = Embedder(device="cpu")
        print("✓ Embedder initialized successfully")
        
        # Batch embed
        print(f"\nBatch embedding {len(test_queries)} queries...")
        vectors = embedder.embed_batch(test_queries)
        print("✓ Batch embedding completed")
        
        # Validate results
        print(f"\n--- Batch Results ---")
        print(f"Number of embeddings: {len(vectors)}")
        print(f"Dimension of each: {len(vectors[0])}")
        
        # Assertions
        print(f"\n--- Assertions ---")
        
        assert len(vectors) == len(test_queries), "Number of embeddings mismatch"
        print(f"✓ Got {len(vectors)} embeddings for {len(test_queries)} queries")
        
        assert all(len(v) == 384 for v in vectors), "Not all embeddings are 384-dimensional"
        print("✓ All embeddings are 384-dimensional")
        
        assert all(abs(sum(x**2 for x in v) ** 0.5 - 1.0) < 1e-5 for v in vectors), "Batch embedding not normalized"
        print("✓ All embeddings are L2 normalized")
        
        print(f"\n{'=' * 60}")
        print("✓ Batch embedding test PASSED")
        print(f"{'=' * 60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test FAILED with error:")
        print(f"  {type(e).__name__}: {str(e)}")
        print(f"{'=' * 60}\n")
        return False


if __name__ == "__main__":
    print("\n")
    result1 = test_embedding_pipeline()
    result2 = test_batch_embedding()
    
    if result1 and result2:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ SOME TESTS FAILED")
        print("=" * 60 + "\n")
        sys.exit(1)
