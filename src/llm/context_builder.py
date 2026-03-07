"""
Context builder for RAG system.

This module converts retrieved chunks into formatted context
with proper metadata and token budget control.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Builds formatted context from retrieved chunks."""
    
    def __init__(self):
        self.default_max_tokens = 1500
        self.estimated_tokens_per_char = 0.25  # Rough estimate
    
    def build_context(
        self, 
        chunks: List[Dict[str, Any]], 
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Build formatted context from retrieved chunks.
        
        Args:
            chunks: List of chunk dictionaries with metadata
            max_tokens: Maximum tokens for context (default: 1500)
            
        Returns:
            Formatted context string
        """
        if max_tokens is None:
            max_tokens = self.default_max_tokens
            
        logger.info(f"Building context from {len(chunks)} chunks with max_tokens={max_tokens}")
        
        context_parts = []
        current_tokens = 0
        
        for i, chunk in enumerate(chunks):
            # Format individual chunk
            chunk_text = self._format_chunk(chunk, i + 1)
            chunk_tokens = self._estimate_tokens(chunk_text)
            
            # Check token budget
            if current_tokens + chunk_tokens > max_tokens:
                logger.warning(f"Token limit reached at chunk {i + 1}, stopping")
                break
            
            context_parts.append(chunk_text)
            current_tokens += chunk_tokens
            
        context = "\n\n".join(context_parts)
        
        logger.info(f"Built context with {current_tokens} estimated tokens from {len(context_parts)} chunks")
        
        return context
    
    def _format_chunk(self, chunk: Dict[str, Any], doc_number: int) -> str:
        """
        Format a single chunk with metadata.
        
        Args:
            chunk: Chunk dictionary with metadata
            doc_number: Document number for formatting
            
        Returns:
            Formatted chunk string
        """
        title = chunk.get('title', 'Unknown Document')
        heading = chunk.get('heading', 'Unknown Section')
        text = chunk.get('text', '')
        
        formatted = f"----- Document {doc_number} -----\n"
        formatted += f"Title: {title}\n"
        formatted += f"Section: {heading}\n\n"
        formatted += f"{text}"
        
        return formatted
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple character-based estimation
        # In production, use a proper tokenizer like tiktoken
        return int(len(text) * self.estimated_tokens_per_char)
    
    def get_context_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about chunks for context building.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Statistics dictionary
        """
        total_text_length = sum(len(chunk.get('text', '')) for chunk in chunks)
        estimated_tokens = self._estimate_tokens(str(total_text_length))
        
        return {
            "chunk_count": len(chunks),
            "total_text_length": total_text_length,
            "estimated_tokens": estimated_tokens,
            "average_chunk_length": total_text_length / len(chunks) if chunks else 0
        }
