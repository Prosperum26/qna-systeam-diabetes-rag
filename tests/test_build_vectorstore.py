#!/usr/bin/env python3
"""
Test script: Build vector store from chunked documents.

This script loads all chunks from data/chunked/, generates embeddings,
and stores them in the vector store for later retrieval.
"""

import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import config
from src.embedder import Embedder
from src.vectorstore import create_vectorstore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_chunks(chunked_dir: Path) -> list[dict]:
    """Load all chunk files from the chunked directory (JSONL format)."""
    chunks = []
    chunk_files = list(chunked_dir.glob("*.jsonl"))
    
    if not chunk_files:
        logger.warning(f"No JSONL files found in {chunked_dir}")
        return chunks
    
    logger.info(f"Found {len(chunk_files)} chunk files")
    
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        chunk_data = json.loads(line)
                        chunks.append(chunk_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line {line_num} in {chunk_file}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to load {chunk_file}: {e}")
    
    return chunks


def main():
    """Main pipeline: load chunks → embed → store."""
    logger.info("Starting vector store building pipeline")
    
    # 1. Load chunks
    chunked_dir = Path("data/chunked")
    if not chunked_dir.exists():
        logger.error(f"Chunked directory not found: {chunked_dir}")
        return
    
    chunks = load_chunks(chunked_dir)
    if not chunks:
        logger.error("No chunks loaded")
        return
    
    logger.info(f"Loaded {len(chunks)} chunks")
    
    # 2. Initialize components
    logger.info("Initializing embedder...")
    embedder = Embedder(
        model_name=config.EMBEDDING_MODEL,
        device="cpu"  # Use CPU for compatibility
    )
    
    logger.info("Initializing vector store...")
    vectorstore = create_vectorstore()
    
    # 3. Extract data for embedding
    logger.info("Extracting texts and metadata...")
    ids = [chunk.get("chunk_id", f"chunk_{i}") for i, chunk in enumerate(chunks)]
    documents = [chunk.get("text", "") for chunk in chunks]
    metadatas = []
    
    for chunk in chunks:
        metadata = {
            "doc_id": chunk.get("doc_id", ""),
            "title": chunk.get("title", ""),
            "heading": chunk.get("heading", ""),
            "position": chunk.get("position", 0),
            "token_count": chunk.get("token_count", 0)
        }
        metadatas.append(metadata)
    
    # 4. Generate embeddings
    logger.info("Generating embeddings...")
    try:
        embeddings = embedder.embed_batch(documents)
        logger.info(f"Generated {len(embeddings)} embeddings")
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return
    
    # 5. Store in vector store
    logger.info("Storing embeddings in vector store...")
    try:
        vectorstore.add_documents(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"Stored {len(embeddings)} vectors")
    except Exception as e:
        logger.error(f"Failed to store embeddings: {e}")
        return
    
    # 6. Persist vector store
    logger.info("Saving vector store...")
    try:
        vectorstore.persist()
        logger.info(f"Vectorstore saved to {config.VECTORSTORE_PATH}")
    except Exception as e:
        logger.error(f"Failed to save vector store: {e}")
        return
    
    logger.info("Vector store building completed successfully!")


if __name__ == "__main__":
    main()
