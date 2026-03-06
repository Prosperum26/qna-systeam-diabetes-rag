#!/usr/bin/env python3
"""
Test script: Retrieval pipeline testing.

This script tests the complete retrieval pipeline:
User query → clean query → embed → retrieve top-k chunks.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import config
from src.embedder import Embedder
from src.vectorstore import create_vectorstore
from src.retriever import VectorRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Test the complete retrieval pipeline."""
    logger.info("Starting retrieval pipeline test")
    
    # 1. Initialize components
    logger.info("Initializing embedder...")
    embedder = Embedder(
        model_name=config.EMBEDDING_MODEL,
        device="cpu"  # Use CPU for compatibility
    )
    
    logger.info("Loading vector store...")
    vectorstore = create_vectorstore()
    
    # Try to load existing vector store
    try:
        vectorstore.load()
        logger.info("Vector store loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        logger.error("Please run test_build_vectorstore.py first")
        return
    
    # 2. Initialize retriever
    logger.info("Initializing retriever...")
    retriever = VectorRetriever(
        vectorstore=vectorstore,
        embedder=embedder,
        top_k=config.TOP_K_RETRIEVAL
    )
    
    # 3. Get user query
    print("\n" + "="*50)
    print("RAG Retrieval Pipeline Test")
    print("="*50)
    
    while True:
        try:
            query = input("\nEnter your question (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                logger.info("Exiting...")
                break
            
            if not query:
                print("Please enter a valid question.")
                continue
            
            # 4. Run retrieval pipeline
            logger.info(f"Processing query: {query}")
            print(f"\nQuery: {query}")
            print(f"\nTop {config.TOP_K_RETRIEVAL} results:\n")
            
            results = retriever.retrieve(query)
            
            if not results:
                print("No results found.")
                continue
            
            # 5. Display results
            for idx, result in enumerate(results, 1):
                score = result.get("score", "N/A")
                text = result.get("text", "").strip()
                
                # Format score
                if isinstance(score, (int, float)):
                    score_str = f"{score:.3f}"
                else:
                    score_str = str(score)
                
                print(f"[{idx}] score={score_str}")
                print(f"{text[:200]}{'...' if len(text) > 200 else ''}")
                
                # Show metadata if available
                metadata_keys = ['title', 'heading', 'doc_id']
                metadata_lines = []
                for key in metadata_keys:
                    value = result.get("metadata", {}).get(key) or result.get(key)
                    if value:
                        metadata_lines.append(f"{key}: {value}")
                
                if metadata_lines:
                    print(f"Metadata: {' | '.join(metadata_lines)}")
                
                print("-" * 50)
            
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user")
            break
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            print(f"Error: {e}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    main()
