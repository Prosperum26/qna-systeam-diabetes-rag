"""
Prompt template for RAG system.

This module provides templates for building prompts that enforce
context-only responses and prevent hallucination.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Template builder for RAG prompts."""
    
    def __init__(self):
        self.base_template = """You are an AI assistant that answers questions using retrieved documents.

Rules:
1. Prefer using the information from the provided context as the primary source.
2. If the context fully answers the question, rely only on the context.
3. If the context provides partial information, you may supplement with general knowledge, but clearly indicate that the context was not sufficient.
4. If the answer cannot be determined from the context at all, respond exactly with:
   "I don't know based on the provided documents."
5. Do NOT fabricate information.
6. If the answer requires combining multiple pieces of context, do so carefully.
7. Cite the relevant part of the context when possible.
8. Always answer in Vietnamese.

Output guidelines:
- If the context is sufficient → answer normally and cite context.
- If the context is partially sufficient → answer and add a note such as:
  "(Lưu ý: thông tin trong context chưa đầy đủ, một phần câu trả lời dựa trên kiến thức chung.)"

Context:
{context}

Question:
{question}

Answer:
Provide a clear and concise answer in Vietnamese."""
    
    def build_prompt(self, context: str, question: str) -> str:
        """
        Build a RAG prompt from context and question.
        
        Args:
            context: Formatted context from retrieved chunks
            question: User question
            
        Returns:
            Complete prompt string
        """
        logger.debug(f"Building prompt for question: {question[:100]}...")
        
        prompt = self.base_template.format(
            context=context,
            question=question
        )
        
        # Log preview (first 200 chars)
        logger.debug(f"Generated prompt preview: {prompt[:200]}...")
        
        return prompt
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get information about the prompt template."""
        return {
            "template_length": len(self.base_template),
            "has_context_constraint": True,
            "has_hallucination_prevention": True,
            "template_type": "rag_context_only"
        }
