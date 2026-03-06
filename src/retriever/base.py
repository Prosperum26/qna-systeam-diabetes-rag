from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseRetriever(ABC):
    """
    Abstract base class for all retriever implementations.
    
    A retriever is responsible for finding relevant document chunks
    based on a user query. Different retrieval strategies can be
    implemented by extending this base class.
    """
    
    @abstractmethod
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for the given query.
        
        Args:
            query: User query string
            
        Returns:
            List of retrieved chunks, where each chunk is a dictionary
            containing at minimum:
            - "text": The chunk content
            - "score": Similarity score (optional)
            - "source": Source document (optional)
            - "chunk_id": Unique chunk identifier (optional)
        """
        pass
