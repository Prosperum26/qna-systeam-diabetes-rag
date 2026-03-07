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
        self.base_template = """You are a helpful assistant.

Use ONLY the context below to answer the question.

If the answer is not present in the context, say:
"I don't know based on the provided documents."

Context:
{context}

Question:
{question}

Answer:"""
    
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
