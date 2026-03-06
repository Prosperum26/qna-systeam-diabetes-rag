"""
Vector store module for RAG pipeline.

Provides a Chroma-based interface for storing
embeddings and running similarity search. Does not perform embedding.
"""

from .base import (
    EXPECTED_EMBEDDING_DIM,
    VectorStore,
)
from .chroma_store import ChromaVectorStore
from .factory import create_vectorstore

__all__ = [
    "VectorStore",
    "ChromaVectorStore",
    "create_vectorstore",
    "EXPECTED_EMBEDDING_DIM",
]
