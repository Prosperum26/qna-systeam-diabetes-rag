#!/usr/bin/env python3
"""
Simple chatbot pipeline that connects retriever and LLM modules.

This module provides a complete RAG chatbot pipeline:
- Retrieves relevant chunks from vector database
- Generates answers using LLM module
- Provides CLI interface for testing
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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

class RAGChatPipeline:
    """
    Complete RAG chatbot pipeline that connects retriever and LLM modules.
    
    Pipeline flow:
    User Query → Retrieve Chunks → Generate Answer → Return Response
    """
    
    def __init__(
        self,
        vectorstore_path: str = "data/vectorstore",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        top_k: int = 5,
        max_context_tokens: int = 1500,
        temperature: float = 0.2
    ):
        """
        Initialize the RAG chat pipeline.
        
        Args:
            vectorstore_path: Path to vector database
            embedding_model: HuggingFace embedding model name
            llm_model: LLM model name for Ollama
            ollama_base_url: Ollama server URL
            top_k: Number of chunks to retrieve
            max_context_tokens: Maximum tokens for context
            temperature: LLM sampling temperature
        """
        self.vectorstore_path = vectorstore_path
        self.top_k = top_k
        self.max_context_tokens = max_context_tokens
        
        # Initialize components (lazy loading)
        self.vectorstore: Optional[ChromaVectorStore] = None
        self.embedder: Optional[Embedder] = None
        self.retriever: Optional[VectorRetriever] = None
        self.generator: Optional[RAGGenerator] = None
        
        # Component configurations
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.ollama_base_url = ollama_base_url
        self.temperature = temperature
        
        logger.info("RAGChatPipeline initialized with lazy loading")
    
    def _ensure_components_loaded(self) -> None:
        """
        Ensure all pipeline components are loaded.
        
        Raises:
            Exception: If any component fails to load
        """
        if self.vectorstore is None:
            self._load_vectorstore()
        
        if self.embedder is None:
            self._load_embedder()
        
        if self.retriever is None:
            self._load_retriever()
        
        if self.generator is None:
            self._load_generator()
    
    def _load_vectorstore(self) -> None:
        """Load vector database from disk."""
        try:
            logger.info(f"Loading vector database from: {self.vectorstore_path}")
            self.vectorstore = ChromaVectorStore(
                persist_path=Path(self.vectorstore_path),
                collection_name="diabetes_knowledge_base"
            )
            
            # Verify database is accessible
            collection = self.vectorstore._get_collection()
            count = collection.count()
            logger.info(f"Vector database loaded with {count} documents")
            
        except Exception as e:
            logger.error(f"Failed to load vector database: {e}")
            raise
    
    def _load_embedder(self) -> None:
        """Load embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.embedding_model}")
            self.embedder = Embedder(
                model_name=self.embedding_model,
                device="cpu",
                normalize=True
            )
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _load_retriever(self) -> None:
        """Load retriever with vector store and embedder."""
        try:
            logger.info("Initializing retriever...")
            self.retriever = VectorRetriever(
                vectorstore=self.vectorstore,
                embedder=self.embedder,
                top_k=self.top_k
            )
            logger.info(f"Retriever initialized with top_k={self.top_k}")
            
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    def _load_generator(self) -> None:
        """Load LLM generator."""
        try:
            logger.info(f"Initializing LLM generator with model: {self.llm_model}")
            self.generator = RAGGenerator(
                ollama_base_url=self.ollama_base_url,
                model=self.llm_model,
                temperature=self.temperature,
                max_context_tokens=self.max_context_tokens
            )
            
            # Check Ollama connectivity
            health = self.generator.check_system_health()
            if not health["ollama_connected"]:
                raise Exception("Ollama server is not running")
            
            logger.info(f"LLM generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM generator: {e}")
            raise
    
    def chat(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            query: User question
            
        Returns:
            Dictionary containing answer, sources, and metadata
            
        Raises:
            Exception: If pipeline processing fails
        """
        logger.info(f"Processing query: {query}")
        
        # Ensure components are loaded
        self._ensure_components_loaded()
        
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant chunks
            logger.info("Retrieving relevant chunks...")
            retrieval_start = time.time()
            
            retrieved_chunks = self.retriever.retrieve(query)
            
            retrieval_time = time.time() - retrieval_start
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.2f}s")
            
            # Step 2: Generate answer
            if retrieved_chunks:
                logger.info("Generating answer...")
                generation_start = time.time()
                
                response = self.generator.generate_answer(
                    query=query,
                    chunks=retrieved_chunks
                )
                
                generation_time = time.time() - generation_start
                total_time = time.time() - start_time
                
                # Prepare result
                result = {
                    "query": query,
                    "answer": response.answer,
                    "sources": response.sources,
                    "chunks_used": response.chunk_count,
                    "context_tokens": response.context_tokens,
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "total_time": total_time,
                    "success": True
                }
                
                logger.info(f"Query processed successfully in {total_time:.2f}s")
                return result
            else:
                # No chunks found
                total_time = time.time() - start_time
                
                result = {
                    "query": query,
                    "answer": "I don't know based on the provided documents.",
                    "sources": [],
                    "chunks_used": 0,
                    "context_tokens": 0,
                    "retrieval_time": retrieval_time,
                    "generation_time": 0,
                    "total_time": total_time,
                    "success": False
                }
                
                logger.warning(f"No relevant chunks found for query: {query}")
                return result
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Failed to process query: {e}")
            
            result = {
                "query": query,
                "answer": f"I apologize, but I encountered an error: {str(e)}",
                "sources": [],
                "chunks_used": 0,
                "context_tokens": 0,
                "retrieval_time": 0,
                "generation_time": 0,
                "total_time": total_time,
                "success": False
            }
            
            return result
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the pipeline components.
        
        Returns:
            Dictionary with pipeline statistics
        """
        try:
            self._ensure_components_loaded()
            
            # Get vector database stats
            collection = self.vectorstore._get_collection()
            doc_count = collection.count()
            
            # Get LLM health
            llm_health = self.generator.check_system_health()
            
            return {
                "vectorstore_path": self.vectorstore_path,
                "document_count": doc_count,
                "embedding_model": self.embedding_model,
                "llm_model": self.llm_model,
                "ollama_connected": llm_health["ollama_connected"],
                "top_k": self.top_k,
                "max_context_tokens": self.max_context_tokens,
                "temperature": self.temperature,
                "components_loaded": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get pipeline stats: {e}")
            return {
                "components_loaded": False,
                "error": str(e)
            }

def print_chat_response(response: Dict[str, Any]) -> None:
    """
    Print chat response in a readable format.
    
    Args:
        response: Response dictionary from chat method
    """
    print(f"\n{'='*60}")
    print("RAG CHATBOT RESPONSE")
    print("="*60)
    print(f"Question: {response['query']}")
    print(f"\nAnswer: {response['answer']}")
    
    if response['sources']:
        print(f"\nSources: {', '.join(response['sources'])}")
    
    print(f"\nPerformance:")
    print(f"- Retrieval time: {response['retrieval_time']:.2f}s")
    print(f"- Generation time: {response['generation_time']:.2f}s")
    print(f"- Total time: {response['total_time']:.2f}s")
    print(f"- Chunks used: {response['chunks_used']}")
    print(f"- Context tokens: {response['context_tokens']}")
    print("="*60)

def cli_chat():
    """
    Command-line interface for the RAG chatbot.
    
    Provides an interactive chat loop where users can ask questions
    and receive answers from the RAG system.
    """
    print("RAG Diabetes Chatbot")
    print("=" * 60)
    print("Welcome! Ask me anything about diabetes.")
    print("Type 'quit', 'exit', or Ctrl+C to stop.")
    print("=" * 60)
    
    # Initialize pipeline
    try:
        pipeline = RAGChatPipeline()
        
        # Show pipeline stats
        stats = pipeline.get_pipeline_stats()
        if stats["components_loaded"]:
            print(f"\nPipeline ready:")
            print(f"- Documents in database: {stats['document_count']}")
            print(f"- Embedding model: {stats['embedding_model']}")
            print(f"- LLM model: {stats['llm_model']}")
            print(f"- Ollama connected: {stats['ollama_connected']}")
            print("=" * 60)
        else:
            print(f"Pipeline initialization failed: {stats['error']}")
            return
        
    except Exception as e:
        print(f"Failed to initialize pipeline: {e}")
        print("\nPlease ensure:")
        print("1. Vector database exists at: data/vectorstore")
        print("2. Ollama server is running: ollama serve")
        print("3. Llama3 model is available: ollama pull llama3")
        return
    
    # Chat loop
    while True:
        try:
            # Get user input
            print("\nYou: ", end="", flush=True)
            query = input().strip()
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Skip empty queries
            if not query:
                continue
            
            # Process query
            print("\nBot: Thinking...", end="", flush=True)
            response = pipeline.chat(query)
            
            # Display response
            print_chat_response(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'quit' to exit.")

def test_sample_queries():
    """
    Test the pipeline with sample diabetes-related queries.
    """
    print("Testing RAG Pipeline with Sample Queries")
    print("=" * 60)
    
    sample_queries = [
        "What are the symptoms of type 2 diabetes?",
        "How is diabetes diagnosed?",
        "What treatments are available for diabetes?",
        "What complications can diabetes cause?",
        "How can diabetes be prevented?"
    ]
    
    try:
        pipeline = RAGChatPipeline()
        
        for i, query in enumerate(sample_queries, 1):
            print(f"\n--- Test Query {i} ---")
            print(f"Question: {query}")
            
            response = pipeline.chat(query)
            print(f"Answer: {response['answer'][:200]}...")
            print(f"Sources: {len(response['sources'])} documents")
            print(f"Time: {response['total_time']:.2f}s")
            print("-" * 40)
        
        print("\nAll sample queries completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    """
    Main execution point for RAG chat pipeline.
    
    Usage:
        python src/pipelines/chat_pipeline.py
    
    Provides CLI interface for interactive chat with the RAG system.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Diabetes Chatbot")
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run sample queries instead of interactive chat"
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_sample_queries()
    else:
        cli_chat()
