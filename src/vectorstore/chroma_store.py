"""
ChromaDB-backed vector store.

Uses cosine distance; converts distance to similarity as score = 1 - distance.
Validates embedding dimension (384).
"""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from .base import EXPECTED_EMBEDDING_DIM, VectorStore


COLLECTION_NAME = "diabetes_knowledge_base"
DEFAULT_BATCH_SIZE = 128


class ChromaVectorStore(VectorStore):
    """Vector store implementation using ChromaDB with cosine distance."""

    def __init__(
        self,
        persist_path: Path,
        collection_name: str = COLLECTION_NAME,
        embedding_dimension: int = EXPECTED_EMBEDDING_DIM,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        self.persist_path = Path(persist_path)
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        self.batch_size = batch_size
        self._client: chromadb.PersistentClient | None = None
        self._collection = None

    def _ensure_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self.persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.persist_path),
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        """Get or create the collection with cosine distance and correct dimension."""
        client = self._ensure_client()
        if self._collection is None:
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents in batches; validates embedding dimension (384)."""
        VectorStore.validate_batch(
            ids, documents, embeddings, metadatas, self.embedding_dimension
        )

        collection = self._get_collection()
        n = len(ids)

        for start in range(0, n, self.batch_size):
            end = min(start + self.batch_size, n)
            batch_ids = ids[start:end]
            batch_docs = documents[start:end]
            batch_embs = embeddings[start:end]
            batch_meta = metadatas[start:end]

            # Chroma expects metadata values to be simple types (str, int, float, bool)
            sanitized = [_sanitize_metadata(m) for m in batch_meta]

            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                embeddings=batch_embs,
                metadatas=sanitized,
            )

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return top-k chunks; converts Chroma cosine distance to similarity score."""
        VectorStore.validate_embedding_dimension(
            query_embedding, self.embedding_dimension
        )

        collection = self._get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # query returns lists of lists (one per query)
        ids = results["ids"][0]
        docs = results["documents"][0]
        meta_list = results["metadatas"][0]
        distances = results["distances"][0]

        # Cosine distance -> similarity: score = 1 - distance
        return [
            {
                "chunk_id": cid,
                "text": doc or "",
                "score": 1.0 - dist,
                "metadata": meta or {},
            }
            for cid, doc, meta, dist in zip(ids, docs, meta_list, distances)
        ]

    def persist(self) -> None:
        """Chroma persists automatically when using PersistentClient."""
        self._ensure_client()
        # No explicit call needed; data is written on add.
        pass

    def load(self, path: Path | None = None) -> "ChromaVectorStore":
        """Load existing store from path; uses persist_path if path is None."""
        load_path = path if path is not None else self.persist_path
        self.persist_path = Path(load_path)
        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_collection(
            name=self.collection_name,
        )
        return self

    @classmethod
    def create(cls, persist_path: Path, **kwargs) -> "ChromaVectorStore":
        """Create a new store (and collection) at the given path."""
        return cls(persist_path=persist_path, **kwargs)


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Ensure metadata values are Chroma-supported types (str, int, float, bool)."""
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out
