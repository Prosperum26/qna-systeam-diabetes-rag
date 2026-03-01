"""
Vector store - lưu embeddings và search similarity.
Dùng ChromaDB (local, đơn giản) hoặc FAISS.
"""
from pathlib import Path
from typing import Optional

# TODO: Implement
# - ChromaDB: persist local, dễ dùng
# - Add documents (text + embedding)
# - Similarity search (query -> top_k chunks)


class VectorStore:
    """Lưu trữ vector và tìm kiếm tương tự."""

    def __init__(self, persist_path: Optional[Path] = None, collection_name: str = "rag_docs"):
        self.persist_path = persist_path or Path("data/vectorstore")
        self.collection_name = collection_name
        self._client = None

    def init_or_load(self) -> "VectorStore":
        """Khởi tạo mới hoặc load từ disk nếu đã có."""
        # TODO: Implement
        raise NotImplementedError("Implement init/load tại đây")

    def add_documents(self, documents: list[dict], embeddings: list[list[float]]) -> None:
        """
        Thêm documents + embeddings vào store.
        documents: [{"content": str, "metadata": dict}, ...]
        """
        # TODO: Implement
        raise NotImplementedError("Implement add_documents tại đây")

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Tìm top_k chunks gần nhất với query.
        Trả về [{"content": str, "metadata": dict, "score": float}, ...]
        """
        # TODO: Implement
        raise NotImplementedError("Implement search tại đây")
