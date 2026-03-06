"""
Factory for creating vector store instances.

Reads VECTORSTORE_PATH from project config.
"""

from pathlib import Path
from typing import Literal

from .base import VectorStore
from .chroma_store import ChromaVectorStore


def create_vectorstore(
    path: Path | None = None,
    store_type: Literal["chroma"] | None = None,
    **kwargs,
) -> VectorStore:
    """Create a vector store instance.

    Args:
        path: Persist path for the store. If None, uses config.VECTORSTORE_PATH.
        store_type: Backend to use ("chroma"). If None, uses config.VECTORSTORE_TYPE.
        **kwargs: Passed to the store constructor (e.g. batch_size, collection_name).

    Returns:
        A new VectorStore instance (not loaded from disk; call .load() if needed).
    """
    try:
        import config
        persist_path = path if path is not None else config.VECTORSTORE_PATH
        backend = store_type if store_type is not None else config.VECTORSTORE_TYPE
    except ImportError:
        if path is None:
            persist_path = Path("data/vectorstore")
        else:
            persist_path = path
        backend = store_type if store_type is not None else "chroma"

    persist_path = Path(persist_path)

    if backend == "chroma":
        return ChromaVectorStore(persist_path=persist_path, **kwargs)
    raise ValueError(
        f"Unknown vector store type: {backend!r}. Use 'chroma'."
    )
