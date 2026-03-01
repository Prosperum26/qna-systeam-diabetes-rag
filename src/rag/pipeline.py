"""
RAG Pipeline: Query -> Embed -> Retrieve -> Build prompt -> Generate.
Orchestrate toàn bộ flow từ câu hỏi đến câu trả lời.
"""
from typing import Optional

# TODO: Implement
# - Nhận question
# - Embed question
# - Search vectorstore -> top_k chunks
# - Build prompt: context + question
# - Gọi LLM generate
# - Return answer


class RAGPipeline:
    """Pipeline RAG end-to-end."""

    def __init__(self, embedder, vectorstore, llm, top_k: int = 5):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.llm = llm
        self.top_k = top_k

    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """
        Nhận câu hỏi, trả về câu trả lời.
        Flow: embed(question) -> search -> build_prompt -> llm.generate
        """
        # TODO: Implement
        raise NotImplementedError("Implement ask logic tại đây")
