import re
import logging

logger = logging.getLogger(__name__)

def clean_query(query: str) -> str:
    """
    Clean and preprocess user query before embedding.
    
    Args:
        query: Raw user query string
        
    Returns:
        Cleaned query string
        
    Example:
        Input: "Triệu chứng tiểu đường???"
        Output: "triệu chứng tiểu đường"
    """
    if not isinstance(query, str):
        logger.warning(f"Query is not a string: {type(query)}")
        return ""
    
    # Convert to lowercase
    cleaned = query.lower()
    
    # Remove punctuation using regex
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    
    # Strip whitespace
    cleaned = cleaned.strip()
    
    logger.debug(f"Query cleaned: '{query}' -> '{cleaned}'")
    
    return cleaned
