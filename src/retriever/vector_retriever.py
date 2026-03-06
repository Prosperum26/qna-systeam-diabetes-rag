import logging
from typing import List, Dict, Any
from .base import BaseRetriever
from ..processors.query_cleaner import clean_query

logger = logging.getLogger(__name__)

class VectorRetriever(BaseRetriever):
    """
    Vector-based retriever that uses embedding similarity to find relevant chunks.
    
    Pipeline:
        User Query → Clean Query → Embed Query → 
        VectorStore Search → Return Top Chunks
    """
    
    def __init__(self, vectorstore, embedder, top_k: int = 5):
        """
        Initialize VectorRetriever.
        
        Args:
            vectorstore: VectorStore instance with similarity_search method
            embedder: Embedding model instance with embed method
            top_k: Number of chunks to retrieve (default: 5)
        """
        self.vectorstore = vectorstore
        self.embedder = embedder
        self.top_k = top_k
        
        logger.info(f"VectorRetriever initialized with top_k={top_k}")
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks from vectorstore.
        
        Args:
            query: User query string
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        # Step 1: Clean query
        clean_q = clean_query(query)
        logger.info(f"Original query: {query}")
        logger.info(f"Cleaned query: {clean_q}")
        
        # Step 2: Embed query
        try:
            query_embedding = self.embedder.embed(clean_q)
            logger.debug(f"Query embedding generated, shape: {len(query_embedding) if hasattr(query_embedding, '__len__') else 'unknown'}")
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []
        
        # Step 3: Vector search
        try:
            results = self.vectorstore.similarity_search(
                query_embedding,
                top_k=self.top_k
            )
            logger.info(f"Retrieved {len(results)} chunks from vectorstore")
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
        
        # Step 4: Log results
        self._log_retrieval_results(results)
        
        return results
    
    @staticmethod
    def _log_retrieval_results(results: List[Dict[str, Any]]) -> None:
        """
        Log retrieved chunks with similarity scores safely.
        
        Args:
            results: List of retrieved chunks
        """
        logger.info(f"Retrieved {len(results)} chunks:")
        
        for idx, result in enumerate(results, 1):
            score = result.get("score")
            text = result.get("text", "").replace("\n", " ")
            
            # Safe score formatting
            if isinstance(score, (int, float)):
                score_str = f"{score:.3f}"
            else:
                score_str = "N/A"
            
            logger.info(
                f"[{idx}] score={score_str} | {text[:100]}..."
            )
