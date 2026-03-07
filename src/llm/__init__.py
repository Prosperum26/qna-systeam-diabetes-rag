"""
LLM module for RAG system.

This module provides components for Retrieval-Augmented Generation
including context building, prompt templating, LLM communication,
and response generation.
"""

import logging

# Configure logging for the LLM module
logging.getLogger(__name__).addHandler(logging.NullHandler())

from .generator import RAGGenerator, RAGResponse
from .context_builder import ContextBuilder
from .prompt_template import PromptTemplate
from .llm_client import OllamaClient

__all__ = [
    "RAGGenerator",
    "RAGResponse", 
    "ContextBuilder",
    "PromptTemplate",
    "OllamaClient"
]
