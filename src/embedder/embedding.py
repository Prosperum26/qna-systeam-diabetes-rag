"""
Embedding local - dùng sentence-transformers hoặc model tương tự.
Chạy trên CPU/GPU local, không cần API.
"""
from typing import Optional

# TODO: Implement
# - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (hỗ trợ tiếng Việt)
# - Hoặc model khác phù hợp


class LocalEmbedder:
    """Embedding model chạy local."""

    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None

    def load(self) -> "LocalEmbedder":
        """Load model vào memory."""
        # TODO: Implement - SentenceTransformer(model_name)
        raise NotImplementedError("Implement load model tại đây")

    def embed_text(self, text: str) -> list[float]:
        """Embed 1 đoạn text, trả về vector."""
        # TODO: Implement
        raise NotImplementedError("Implement embed_text tại đây")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed nhiều documents (batch)."""
        # TODO: Implement
        raise NotImplementedError("Implement embed_documents tại đây")
