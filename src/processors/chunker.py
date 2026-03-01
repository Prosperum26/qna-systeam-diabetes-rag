"""
Chia documents thành chunks phù hợp cho embedding.
Có thể dùng RecursiveCharacterTextSplitter (LangChain) hoặc custom logic.
"""
from typing import Optional

# TODO: Implement
# - Load documents từ data/raw hoặc từ crawler output
# - Chunk theo size + overlap
# - Trả về list Document (LangChain) hoặc list dict


class DocumentChunker:
    """Chia văn bản thành chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_documents(self, documents: list[dict]) -> list:
        """
        Chunk list documents.
        Input: [{"content": str, "url": str, "title": str}, ...]
        Output: list Document (LangChain) hoặc list {"content": str, "metadata": dict}
        """
        # TODO: Implement - dùng LangChain RecursiveCharacterTextSplitter
        raise NotImplementedError("Implement chunk logic tại đây")

    def load_and_chunk(self, input_path: str) -> list:
        """Load từ file (JSON/text) rồi chunk."""
        # TODO: Implement
        raise NotImplementedError("Implement load + chunk tại đây")
