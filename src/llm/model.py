"""
LLM local - Ollama, llama.cpp, hoặc API tương thích OpenAI.
Generate câu trả lời dựa trên context + question.
"""
from typing import Optional

# TODO: Implement
# - Ollama: ollama run llama3.2
# - Hoặc langchain Ollama/ChatOllama


class LocalLLM:
    """LLM chạy local (Ollama)."""

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self._client = None

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate response từ prompt.
        system_prompt: hướng dẫn cho model (vd: "Bạn là trợ lý về bệnh tiểu đường...")
        """
        # TODO: Implement - gọi Ollama API
        raise NotImplementedError("Implement generate tại đây")
