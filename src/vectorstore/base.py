"""
Abstract base class for vector store backends.

The vector store is responsible only for:
- Storing embeddings and associated documents/metadata
- Indexing vectors for fast similarity search
- Returning top-k results with scores

It does NOT embed text, clean text, or apply retrieval filtering.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


# Expected embedding dimension (paraphrase-multilingual-MiniLM-L12-v2)
EXPECTED_EMBEDDING_DIM = 384


class VectorStore(ABC):
    """Abstract interface for vector store implementations."""

    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents with pre-computed embeddings to the store.

        Args:
            ids: Unique chunk identifiers (e.g. chunk_id).
            documents: Raw text of each chunk.
            embeddings: Pre-computed embedding vectors (L2-normalized for cosine).
            metadatas: Metadata dict per chunk (e.g. title, heading, position).
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return top-k most similar chunks for a query embedding.

        Args:
            query_embedding: Pre-computed query vector (same dimension as stored).
            top_k: Number of results to return.

        Returns:
            List of dicts with keys: chunk_id, text, score, metadata.
            Score is similarity (higher = more similar); e.g. cosine in [0, 1].
        """
        pass

    @abstractmethod
    def persist(self) -> None:
        """Persist the vector store to disk."""
        pass

    @abstractmethod
    def load(self, path: Path | None = None) -> "VectorStore":
        """Load the vector store from disk.

        Args:
            path: Optional path to load from; implementation may use instance path.

        Returns:
            self for method chaining.
        """
        pass

    @staticmethod
    def validate_embedding_dimension(embedding: list[float], dimension: int = EXPECTED_EMBEDDING_DIM) -> None:
        """Validate that an embedding has the expected dimension.

        Raises:
            ValueError: If dimension does not match.
        """
        if len(embedding) != dimension:
            raise ValueError(
                f"Embedding dimension mismatch: expected {dimension}, got {len(embedding)}"
            )

    @staticmethod
    def validate_batch(
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        dimension: int = EXPECTED_EMBEDDING_DIM,
    ) -> None:
        """Validate that batch lengths match and embedding dimensions are correct.

        Raises:
            ValueError: If lengths differ or any embedding has wrong dimension.
        """
        n = len(ids)
        if len(documents) != n or len(embeddings) != n or len(metadatas) != n:
            raise ValueError(
                f"Batch length mismatch: ids={n}, documents={len(documents)}, "
                f"embeddings={len(embeddings)}, metadatas={len(metadatas)}"
            )
        for i, emb in enumerate(embeddings):
            VectorStore.validate_embedding_dimension(emb, dimension)
