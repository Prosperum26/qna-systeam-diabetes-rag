#!/usr/bin/env python3
"""
Test script for complete RAG pipeline with real vector database.

This script tests the full RAG flow:
1. Load existing vector database
2. Use retriever to get relevant chunks
3. Send chunks to LLM module
4. Generate answer based on retrieved context
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to path for imports
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Add parent directory to sys.modules to fix relative imports
import sys
import importlib.util

# Create a dummy module for src to fix relative imports
import types
src_module = types.ModuleType('src')
sys.modules['src'] = src_module

from vectorstore import ChromaVectorStore
from embedder import Embedder
from retriever import VectorRetriever
from llm import RAGGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_vector_database(vectorstore_path: str) -> ChromaVectorStore:
    """
    Load existing vector database from disk.
    
    Args:
        vectorstore_path: Path to the vector database directory
        
    Returns:
        Loaded ChromaVectorStore instance
        
    Raises:
        Exception: If vector database cannot be loaded
    """
    logger.info(f"Loading vector database from: {vectorstore_path}")
    
    try:
        vectorstore = ChromaVectorStore(
            persist_path=Path(vectorstore_path),
            collection_name="diabetes_knowledge_base"
        )
        
        # Test if database is accessible
        client = vectorstore._ensure_client()
        collection = vectorstore._get_collection()
        count = collection.count()
        
        logger.info(f"Vector database loaded successfully with {count} documents")
        return vectorstore
        
    except Exception as e:
        logger.error(f"Failed to load vector database: {e}")
        raise

def load_embedding_model() -> Embedder:
    """
    Load embedding model for query processing.
    
    Returns:
        Initialized Embedder instance
    """
    logger.info("Loading embedding model...")
    
    try:
        embedder = Embedder(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            device="cpu",
            normalize=True
        )
        
        logger.info("Embedding model loaded successfully")
        return embedder
        
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise

def initialize_retriever(vectorstore: ChromaVectorStore, embedder: Embedder) -> VectorRetriever:
    """
    Initialize the retriever with vector store and embedder.
    
    Args:
        vectorstore: Loaded vector database
        embedder: Initialized embedding model
        
    Returns:
        Initialized VectorRetriever instance
    """
    logger.info("Initializing retriever...")
    
    try:
        retriever = VectorRetriever(
            vectorstore=vectorstore,
            embedder=embedder,
            top_k=5
        )
        
        logger.info(f"Retriever initialized with top_k=5")
        return retriever
        
    except Exception as e:
        logger.error(f"Failed to initialize retriever: {e}")
        raise

def initialize_llm_generator() -> RAGGenerator:
    """
    Initialize the LLM generator.
    
    Returns:
        Initialized RAGGenerator instance
        
    Raises:
        Exception: If LLM cannot be initialized
    """
    logger.info("Initializing LLM generator...")
    
    try:
        generator = RAGGenerator(
            ollama_base_url="http://localhost:11434",
            model="llama3",
            temperature=0.2,
            max_context_tokens=1500
        )
        
        # Check Ollama connectivity
        health = generator.check_system_health()
        if not health["ollama_connected"]:
            logger.error("Ollama server is not running")
            raise Exception("Ollama server not accessible")
        
        logger.info(f"LLM generator initialized with model: {health['model']}")
        return generator
        
    except Exception as e:
        logger.error(f"Failed to initialize LLM generator: {e}")
        raise

def print_retrieved_chunks(chunks: list) -> None:
    """
    Print retrieved chunks with metadata in a readable format.
    
    Args:
        chunks: List of retrieved chunk dictionaries
    """
    print("\n" + "="*80)
    print("RETRIEVED CHUNKS")
    print("="*80)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Score: {chunk.get('score', 'N/A')}")
        print(f"Document ID: {chunk.get('doc_id', 'N/A')}")
        print(f"Title: {chunk.get('title', 'N/A')}")
        print(f"Section: {chunk.get('heading', 'N/A')}")
        print(f"Position: {chunk.get('position', 'N/A')}")
        print(f"Text preview: {chunk.get('text', '')[:200]}...")
        print("-" * 40)
    
    print("="*80)

def test_rag_pipeline():
    """
    Test the complete RAG pipeline with real vector database.
    
    Returns:
        True if test successful, False otherwise
    """
    logger.info("Starting RAG pipeline test with real vector database")
    
    try:
        # Step 1: Load vector database
        vectorstore_path = "data/vectorstore"
        vectorstore = load_vector_database(vectorstore_path)
        
        # Step 2: Load embedding model
        embedder = load_embedding_model()
        
        # Step 3: Initialize retriever
        retriever = initialize_retriever(vectorstore, embedder)
        
        # Step 4: Initialize LLM generator
        generator = initialize_llm_generator()
        
        # Step 5: Test query
        test_query = "Triệu chứng của bệnh đột tử ở người bị tiểu đường."
        logger.info(f"Testing query: {test_query}")
        
        # Step 6: Retrieve relevant chunks
        logger.info("Retrieving relevant chunks...")
        retrieval_start = time.time()
        
        retrieved_chunks = retriever.retrieve(test_query)
        
        retrieval_time = time.time() - retrieval_start
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.2f}s")
        
        # Step 7: Print retrieved chunks
        print_retrieved_chunks(retrieved_chunks)
        
        # Step 8: Generate answer using LLM
        if retrieved_chunks:
            logger.info("Generating answer using LLM...")
            generation_start = time.time()
            
            response = generator.generate_answer(
                query=test_query,
                chunks=retrieved_chunks
            )
            
            generation_time = time.time() - generation_start
            total_time = retrieval_time + generation_time
            
            # Step 9: Display results
            print(f"\n{'='*80}")
            print("RAG PIPELINE RESULTS")
            print("="*80)
            print(f"QUESTION: {test_query}")
            print(f"\nANSWER:\n{response.answer}")
            print(f"\nSOURCES: {', '.join(response.sources)}")
            print(f"\nPERFORMANCE METRICS:")
            print(f"- Retrieval time: {retrieval_time:.2f}s")
            print(f"- Generation time: {generation_time:.2f}s")
            print(f"- Total time: {total_time:.2f}s")
            print(f"- Chunks used: {response.chunk_count}")
            print(f"- Context tokens: {response.context_tokens}")
            print(f"- Answer length: {len(response.answer)} chars")
            print("="*80)
            
            logger.info(f"RAG pipeline test completed successfully")
            logger.info(f"Total time: {total_time:.2f}s")
            
            return True
        else:
            logger.warning("No chunks retrieved for the query")
            print("\nNo relevant chunks found for the query.")
            return False
            
    except Exception as e:
        logger.error(f"RAG pipeline test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        print("\nPlease ensure:")
        print("1. Vector database exists at: data/vectorstore")
        print("2. Ollama server is running: ollama serve")
        print("3. Llama3 model is available: ollama pull llama3")
        print("4. All required packages are installed")
        return False

def test_multiple_queries():
    """
    Test the RAG pipeline with multiple diabetes-related queries.
    
    Returns:
        True if all tests successful, False otherwise
    """
    test_queries = [
        "Triệu chứng của bệnh đột tử ở người bị tiểu đường.",
        "Các dấu hiệu của tiểu đường không kiểm soát.",
        "Cách tính lượng đường trong thức ăn.",
        "Đột biến gen có gây bệnh tiểu đường không?"
    ]
    
    logger.info("Testing RAG pipeline with multiple queries")
    
    try:
        # Initialize components once
        vectorstore = load_vector_database("data/vectorstore")
        embedder = load_embedding_model()
        retriever = initialize_retriever(vectorstore, embedder)
        generator = initialize_llm_generator()
        
        print("\n" + "="*80)
        print("MULTIPLE QUERY TEST")
        print("="*80)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Query {i} ---")
            print(f"Question: {query}")
            
            try:
                # Retrieve chunks
                chunks = retriever.retrieve(query)
                
                if chunks:
                    # Generate answer
                    response = generator.generate_answer(query, chunks)
                    
                    print(f"Answer: {response.answer[:200]}...")
                    print(f"Sources: {len(response.sources)} documents")
                    print(f"Chunks used: {response.chunk_count}")
                else:
                    print("No relevant chunks found")
                    
            except Exception as e:
                print(f"Error: {e}")
            
            print("-" * 60)
        
        print("="*80)
        logger.info("Multiple query test completed")
        return True
        
    except Exception as e:
        logger.error(f"Multiple query test failed: {e}")
        return False

if __name__ == "__main__":
    """
    Main execution point for RAG retrieval test.
    
    Usage:
        python tests/test_rag_retrieval.py
    
    This script tests the complete RAG pipeline with real vector database.
    """
    print("RAG Retrieval Test Script")
    print("=" * 80)
    print("Testing complete RAG pipeline with real vector database...")
    print()
    
    # Run single query test
    success = test_rag_pipeline()
    
    if success:
        print("\n" + "="*80)
        print("Optional: Run multiple query test? (y/n): ", end="")
        try:
            choice = input().lower().strip()
            if choice == 'y':
                test_multiple_queries()
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
    
    print("\n" + "="*80)
    if success:
        print("✅ RAG retrieval test completed successfully!")
        print("The pipeline is ready for integration.")
    else:
        print("❌ RAG retrieval test failed!")
        print("Please check the error messages above.")
    print("="*80)
