"""
Retriever module for RAG system.

This module provides components for retrieving relevant document chunks
based on user queries using vector similarity search.
"""

from .base import BaseRetriever
from .vector_retriever import VectorRetriever

__all__ = [
    "BaseRetriever",
    "VectorRetriever"
]
