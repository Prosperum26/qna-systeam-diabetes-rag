"""
RAG generator orchestrator.

This module orchestrates the complete RAG generation pipeline
from chunks to final response with source attribution.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .context_builder import ContextBuilder
from .prompt_template import PromptTemplate
from .llm_client import OllamaClient

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    """Response object for RAG generation."""
    answer: str
    sources: List[str]
    chunk_count: int
    context_tokens: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "chunk_count": self.chunk_count,
            "context_tokens": self.context_tokens
        }

class RAGGenerator:
    """Orchestrates the complete RAG generation pipeline."""
    
    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "llama3",
        temperature: float = 0.2,
        max_context_tokens: int = 1500
    ):
        """
        Initialize RAG generator.
        
        Args:
            ollama_base_url: Ollama server URL
            model: LLM model name
            temperature: Sampling temperature
            max_context_tokens: Maximum tokens for context
        """
        self.context_builder = ContextBuilder()
        self.prompt_template = PromptTemplate()
        self.llm_client = OllamaClient(
            base_url=ollama_base_url,
            model=model,
            temperature=temperature
        )
        self.max_context_tokens = max_context_tokens
        
        logger.info(f"Initialized RAG generator with model={model}, max_context_tokens={max_context_tokens}")
    
    def generate_answer(
        self, 
        query: str, 
        chunks: List[Dict[str, Any]],
        max_tokens: Optional[int] = None
    ) -> RAGResponse:
        """
        Generate answer from query and retrieved chunks.
        
        Args:
            query: User question
            chunks: Retrieved chunks with metadata
            max_tokens: Override max context tokens
            
        Returns:
            RAGResponse with answer and sources
        """
        logger.info(f"Generating answer for query: {query[:100]}...")
        logger.info(f"Processing {len(chunks)} retrieved chunks")
        
        # Use provided max_tokens or default
        context_limit = max_tokens or self.max_context_tokens
        
        # Step 1: Build context from chunks
        context = self.context_builder.build_context(chunks, context_limit)
        context_tokens = self.context_builder._estimate_tokens(context)
        
        # Step 2: Build prompt using context + query
        prompt = self.prompt_template.build_prompt(context, query)
        
        # Step 3: Send prompt to LLM
        try:
            answer = self.llm_client.generate(prompt)
            logger.info(f"Generated answer with length: {len(answer)}")
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            answer = "I apologize, but I encountered an error while generating the response."
        
        # Step 4: Extract sources from chunk metadata
        sources = self._extract_sources(chunks)
        
        # Create response object
        response = RAGResponse(
            answer=answer,
            sources=sources,
            chunk_count=len(chunks),
            context_tokens=context_tokens
        )
        
        logger.info(f"Generated RAG response with {len(sources)} sources")
        
        return response
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract unique sources from chunk metadata.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of unique source identifiers
        """
        sources = set()
        
        for chunk in chunks:
            # Prefer title over doc_id as source
            title = chunk.get('title')
            doc_id = chunk.get('doc_id')
            
            if title and title != 'Unknown Document':
                sources.add(title)
            elif doc_id:
                sources.add(doc_id)
        
        return list(sources)
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check the health of the RAG system components.
        
        Returns:
            Health status dictionary
        """
        ollama_connected = self.llm_client.check_connection()
        
        return {
            "ollama_connected": ollama_connected,
            "model": self.llm_client.model,
            "max_context_tokens": self.max_context_tokens,
            "components_initialized": True
        }
    
    def get_generator_config(self) -> Dict[str, Any]:
        """
        Get generator configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "llm_config": self.llm_client.get_model_info(),
            "max_context_tokens": self.max_context_tokens,
            "prompt_template_info": self.prompt_template.get_template_info()
        }
