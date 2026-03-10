#!/usr/bin/env python3
"""
Knowledge building pipeline for RAG system.

Orchestrates the complete pipeline:
1. Load documents from JSON files
2. Chunk documents into smaller pieces
3. Generate embeddings for chunks
4. Store vectors in vector database
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

import torch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chunking.chunker import HybridChunker
from chunking.token_counter import TokenCounter
from embedder import Embedder
from vectorstore import create_vectorstore, EXPECTED_EMBEDDING_DIM, VectorStore


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def load_documents(data_dir: str = "data/documents") -> List[Dict]:
    """
    Load cleaned and deduplicated documents from JSON files.
    
    Args:
        data_dir: Directory containing document JSON files
        
    Returns:
        List of document dictionaries
    """
    documents = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")
    
    json_files = list(data_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")
    
    logging.info(f"Found {len(json_files)} JSON files in {data_dir}")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            logging.error(f"Failed to load {file_path}: {e}")
            continue
    
    logging.info(f"Successfully loaded {len(documents)} documents")
    return documents


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """
    Chunk documents into smaller pieces for embedding.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        List of chunk dictionaries
    """
    logging.info("Starting document chunking...")
    
    # Initialize chunker
    token_counter = TokenCounter()
    chunker = HybridChunker(
        token_counter=token_counter,
        max_tokens_per_chunk=450,
        chunk_size=400,
        overlap=60,
        min_section_tokens=120
    )
    
    all_chunks = []
    
    for i, doc in enumerate(documents):
        try:
            chunks = chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            logging.info(f"Document {i+1}/{len(documents)}: {len(chunks)} chunks")
        except Exception as e:
            logging.error(f"Failed to chunk document {doc.get('doc_id', 'unknown')}: {e}")
            continue
    
    logging.info(f"Generated {len(all_chunks)} total chunks from {len(documents)} documents")
    return all_chunks


def generate_embeddings(chunks: List[Dict], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for all chunks.
    
    Args:
        chunks: List of chunk dictionaries
        batch_size: Batch size for embedding generation
        
    Returns:
        List of embedding vectors
    """
    logging.info("Starting embedding generation...")
    
    # Initialize embedder
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")
    
    embedder = Embedder(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device=device,
        normalize=True
    )
    
    # Extract text from chunks
    texts = [chunk.get("text", "") for chunk in chunks]
    embeddings = []
    
    # Process in batches
    total_batches = (len(texts) + batch_size - 1) // batch_size
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        try:
            batch_embeddings = embedder.embed_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            logging.info(f"Batch {batch_num}/{total_batches}: {len(batch_embeddings)} embeddings generated")
        except Exception as e:
            logging.error(f"Failed to embed batch {batch_num}: {e}")
            # Add zero embeddings for failed batch to maintain alignment
            zero_emb = [0.0] * EXPECTED_EMBEDDING_DIM
            embeddings.extend([zero_emb] * len(batch_texts))
    
    logging.info(f"Generated {len(embeddings)} embeddings")
    return embeddings


def store_vectors(chunks: List[Dict], embeddings: List[List[float]], store_path: str = "vectorstore") -> None:
    """
    Store chunks and embeddings in vector database.
    
    Args:
        chunks: List of chunk dictionaries
        embeddings: List of embedding vectors
        store_path: Path for vector store persistence
    """
    logging.info("Starting vector storage...")
    
    # Create vector store
    vectorstore = create_vectorstore(
        path=Path(store_path),
        store_type="chroma"
    )
    
    # Prepare data for storage
    ids = [chunk.get("chunk_id", f"chunk_{i}") for i, chunk in enumerate(chunks)]
    documents = [chunk.get("text", "") for chunk in chunks]
    metadatas = []
    
    for chunk in chunks:
        metadata = {
            "doc_id": chunk.get("doc_id", ""),
            "title": chunk.get("title", ""),
            "heading": chunk.get("heading", ""),
            "position": chunk.get("position", 0),
            "url": chunk.get("url", ""),
            "category": chunk.get("category", "")
        }
        metadatas.append(metadata)
    
    # Validate batch
    VectorStore.validate_batch(ids, documents, embeddings, metadatas)
    
    # Store in batches
    batch_size = 128
    total_batches = (len(ids) + batch_size - 1) // batch_size
    
    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        batch_ids = ids[i:batch_end]
        batch_documents = documents[i:batch_end]
        batch_embeddings = embeddings[i:batch_end]
        batch_metadatas = metadatas[i:batch_end]
        
        batch_num = i // batch_size + 1
        
        try:
            vectorstore.add_documents(
                ids=batch_ids,
                documents=batch_documents,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas
            )
            logging.info(f"Batch {batch_num}/{total_batches}: {len(batch_ids)} vectors stored")
        except Exception as e:
            logging.error(f"Failed to store batch {batch_num}: {e}")
    
    # Persist to disk
    try:
        vectorstore.persist()
        logging.info(f"Vector store successfully persisted to {store_path}")
    except Exception as e:
        logging.error(f"Failed to persist vector store: {e}")
        raise
    
    logging.info("Vector storage completed successfully")


def run_pipeline(
    data_dir: str = "data/documents",
    store_path: str = "data/vectorstore",
    batch_size: int = 32
) -> None:
    """
    Run the complete knowledge building pipeline.
    
    Args:
        data_dir: Directory containing document JSON files
        store_path: Path for vector store persistence
        batch_size: Batch size for embedding generation
    """
    logging.info("Starting knowledge building pipeline...")
    
    try:
        # Step 1: Load documents
        documents = load_documents(data_dir)
        
        # Step 2: Chunk documents
        chunks = chunk_documents(documents)
        
        # Step 3: Generate embeddings
        embeddings = generate_embeddings(chunks, batch_size)
        
        # Step 4: Store vectors
        store_vectors(chunks, embeddings, store_path)
        
        logging.info("Knowledge building pipeline completed successfully!")
        logging.info(f"Processed {len(documents)} documents → {len(chunks)} chunks → {len(embeddings)} embeddings")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise


def main() -> None:
    """Main entry point for command line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build knowledge base for RAG system")
    parser.add_argument(
        "--data-dir",
        default="data/documents",
        help="Directory containing document JSON files (default: data/documents)"
    )
    parser.add_argument(
        "--store-path",
        default="data/vectorstore",
        help="Path for vector store persistence (default: data/vectorstore)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation (default: 32)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run pipeline
    run_pipeline(
        data_dir=args.data_dir,
        store_path=args.store_path,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
