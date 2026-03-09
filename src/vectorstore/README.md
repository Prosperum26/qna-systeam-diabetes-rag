# Vector Store Module

Module này cung cấp abstraction và implementations cho việc lưu trữ và tìm kiếm vector embeddings, sử dụng ChromaDB để thực hiện similarity search operations trong hệ thống RAG.

## 🎯 Mục tiêu

- Lưu trữ vector embeddings một cách hiệu quả
- Cung cấp fast similarity search cho retrieval operations
- Support persistent storage và loading
- Validate embedding dimensions và data integrity
- Cung cấp flexible interface cho different vector store backends

## 🏗️ Kiến trúc

```
src/vectorstore/
├── __init__.py
├── base.py            # Abstract base class for vector stores
├── chroma_store.py    # ChromaDB implementation
├── factory.py         # Factory for creating vector stores
└── README.md         # This file
```

## 🔧 Components

### VectorStore Base Class (`base.py`)

Abstract interface định nghĩa contract cho tất cả vector store implementations:

```python
class VectorStore(ABC):
    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents with pre-computed embeddings to store."""
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return top-k most similar chunks for a query embedding."""
    
    @abstractmethod
    def persist(self) -> None:
        """Persist vector store to disk."""
    
    @abstractmethod
    def load(self, path: Path | None = None) -> "VectorStore":
        """Load vector store from disk."""
```

**Features:**
- Embedding dimension validation (384 for MiniLM)
- Batch data validation
- Standardized interface cho multiple backends
- Type hints và documentation

### ChromaVectorStore (`chroma_store.py`)

ChromaDB implementation với cosine similarity:

```python
class ChromaVectorStore(VectorStore):
    def __init__(
        self,
        persist_path: Path,
        collection_name: str = "diabetes_knowledge_base",
        embedding_dimension: int = 384,
        batch_size: int = 128
    ):
```

**Features:**
- Persistent storage với ChromaDB
- Cosine distance similarity search
- Batch processing cho efficiency
- Automatic collection management
- Error handling và validation

### VectorStore Factory (`factory.py`)

Factory pattern cho creating vector store instances:

```python
def create_vectorstore(
    path: Path | None = None,
    store_type: Literal["chroma"] | None = None,
    **kwargs,
) -> VectorStore:
    """Create a vector store instance with configuration."""
```

## 🚀 Usage

### Basic Vector Store Operations

```python
from src.vectorstore.factory import create_vectorstore
from src.embedder import Embedder

# Create vector store
vectorstore = create_vectorstore(
    path="data/vectorstore",
    store_type="chroma"
)

# Load existing store
vectorstore.load()

# Prepare data
ids = ["chunk_1", "chunk_2", "chunk_3"]
documents = ["Diabetes overview...", "Symptoms include...", "Treatment options..."]
metadatas = [
    {"title": "Diabetes Overview", "heading": "Introduction"},
    {"title": "Symptoms", "heading": "Common Signs"},
    {"title": "Treatment", "heading": "Medical Care"}
]

# Generate embeddings
embedder = Embedder()
embeddings = [embedder.embed(doc) for doc in documents]

# Add to store
vectorstore.add_documents(ids, documents, embeddings, metadatas)

# Persist to disk
vectorstore.persist()
```

### Similarity Search

```python
# Query embedding
query = "What are diabetes symptoms?"
query_embedding = embedder.embed(query)

# Search for similar documents
results = vectorstore.similarity_search(
    query_embedding=query_embedding,
    top_k=5
)

# Process results
for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text'][:100]}...")
    print(f"Metadata: {result['metadata']}")
    print("---")
```

### Factory Pattern Usage

```python
from src.vectorstore.factory import create_vectorstore

# Create with default configuration
vectorstore = create_vectorstore()

# Create with custom path
vectorstore = create_vectorstore(path="custom/vectorstore/path")

# Create with additional parameters
vectorstore = create_vectorstore(
    path="data/vectorstore",
    batch_size=64,
    collection_name="medical_kb"
)
```

## 📊 Data Format

### Input Data Structure

```python
# Documents to add
ids = ["doc_001_chunk_0", "doc_001_chunk_1"]
documents = [
    "Type 2 diabetes is a chronic condition...",
    "Common symptoms include increased thirst..."
]
embeddings = [
    [0.1234, -0.5678, ...],  # 384-dimensional vector
    [0.2345, -0.6789, ...]   # 384-dimensional vector
]
metadatas = [
    {
        "title": "Diabetes Overview",
        "heading": "Introduction",
        "doc_id": "doc_001",
        "position": 0
    },
    {
        "title": "Diabetes Overview", 
        "heading": "Symptoms",
        "doc_id": "doc_001",
        "position": 1
    }
]
```

### Search Results Format

```python
results = [
    {
        "id": "doc_001_chunk_0",
        "text": "Type 2 diabetes is a chronic condition...",
        "score": 0.89,  # Cosine similarity (0-1)
        "metadata": {
            "title": "Diabetes Overview",
            "heading": "Introduction",
            "doc_id": "doc_001",
            "position": 0
        }
    },
    {
        "id": "doc_002_chunk_3",
        "text": "Diabetes affects how your body processes glucose...",
        "score": 0.85,
        "metadata": {
            "title": "Understanding Diabetes",
            "heading": "Pathophysiology",
            "doc_id": "doc_002", 
            "position": 3
        }
    }
]
```

## ⚙️ Configuration

### VectorStore Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `persist_path` | Path | Required | Directory for storing vectors |
| `collection_name` | str | "diabetes_knowledge_base" | ChromaDB collection name |
| `embedding_dimension` | int | 384 | Vector dimension (MiniLM) |
| `batch_size` | int | 128 | Batch size for operations |

### ChromaDB Settings

```python
# Custom ChromaDB configuration
vectorstore = ChromaVectorStore(
    persist_path=Path("data/vectorstore"),
    collection_name="custom_collection",
    embedding_dimension=768,  # For larger models
    batch_size=64
)

# ChromaDB client settings
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="data/vectorstore",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)
```

## 🔍 Advanced Features

### Batch Processing

```python
class BatchProcessor:
    """Efficient batch processing for large datasets."""
    
    def __init__(self, vectorstore, batch_size=1000):
        self.vectorstore = vectorstore
        self.batch_size = batch_size
    
    def add_large_dataset(self, chunks):
        """Add chunks in batches to avoid memory issues."""
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            
            ids = [chunk['chunk_id'] for chunk in batch]
            documents = [chunk['content'] for chunk in batch]
            embeddings = [chunk['embedding'] for chunk in batch]
            metadatas = [{k: v for k, v in chunk.items() 
                        if k not in ['chunk_id', 'content', 'embedding']} 
                       for chunk in batch]
            
            self.vectorstore.add_documents(ids, documents, embeddings, metadatas)
            
            if i % (self.batch_size * 10) == 0:
                print(f"Processed {i + len(batch)} chunks...")
        
        self.vectorstore.persist()
```

### Metadata Filtering

```python
class FilteredVectorStore(ChromaVectorStore):
    """Vector store with metadata filtering capabilities."""
    
    def search_with_filters(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict = None
    ) -> list[dict[str, Any]]:
        """Search with optional metadata filters."""
        # Get base results
        results = self.similarity_search(query_embedding, top_k * 2)  # Get more for filtering
        
        # Apply filters
        if filters:
            filtered_results = []
            for result in results:
                metadata = result.get('metadata', {})
                match = True
                
                for key, value in filters.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                
                if match:
                    filtered_results.append(result)
            
            results = filtered_results[:top_k]
        
        return results
```

### Vector Store Maintenance

```python
class VectorStoreManager:
    """Utilities for vector store maintenance."""
    
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
    
    def get_statistics(self) -> dict:
        """Get vector store statistics."""
        collection = self.vectorstore._get_collection()
        count = collection.count()
        
        return {
            "total_documents": count,
            "collection_name": self.vectorstore.collection_name,
            "embedding_dimension": self.vectorstore.embedding_dimension,
            "persist_path": str(self.vectorstore.persist_path)
        }
    
    def backup_store(self, backup_path: Path):
        """Create backup of vector store."""
        import shutil
        shutil.copytree(
            self.vectorstore.persist_path,
            backup_path,
            dirs_exist_ok=True
        )
    
    def reset_store(self):
        """Reset vector store (use with caution)."""
        collection = self.vectorstore._get_collection()
        collection.delete(where={})  # Delete all documents
        self.vectorstore.persist()
```

## 🧪 Testing

```bash
# Run vector store tests
python -m pytest tests/test_vectorstore.py

# Test with sample data
python -c "
from src.vectorstore.factory import create_vectorstore
from src.embedder import Embedder

# Create test store
store = create_vectorstore(path='test_vectorstore')

# Add test data
embedder = Embedder()
test_embedding = embedder.embed('test document')

store.add_documents(
    ids=['test_1'],
    documents=['test document content'],
    embeddings=[test_embedding],
    metadatas=[{'title': 'Test'}]
)

# Search
results = store.similarity_search(test_embedding, top_k=1)
print(f'Found {len(results)} results')
"
```

### Performance Testing

```python
import time
import numpy as np
from src.vectorstore.factory import create_vectorstore

def benchmark_vector_store(vectorstore, num_queries=100):
    """Benchmark vector store performance."""
    # Generate random query embeddings
    query_embeddings = [
        np.random.rand(384).tolist() for _ in range(num_queries)
    ]
    
    # Benchmark search
    times = []
    for query_emb in query_embeddings:
        start_time = time.time()
        results = vectorstore.similarity_search(query_emb, top_k=10)
        end_time = time.time()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    print(f"Average search time: {avg_time:.3f}s")
    print(f"Queries per second: {1/avg_time:.1f}")
    
    return times
```

## 🔧 Customization

### Custom Vector Store Implementation

```python
class CustomVectorStore(VectorStore):
    """Custom vector store implementation."""
    
    def __init__(self, persist_path: Path):
        self.persist_path = persist_path
        self.vectors = {}
        self.metadata = {}
    
    def add_documents(self, ids, documents, embeddings, metadatas):
        """Add documents to custom store."""
        for id, doc, emb, meta in zip(ids, documents, embeddings, metadatas):
            self.vectors[id] = emb
            self.metadata[id] = {
                'text': doc,
                'metadata': meta
            }
    
    def similarity_search(self, query_embedding, top_k):
        """Custom similarity search."""
        similarities = []
        
        for id, vector in self.vectors.items():
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, vector)
            similarities.append((id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Format results
        results = []
        for id, score in similarities[:top_k]:
            results.append({
                'id': id,
                'text': self.metadata[id]['text'],
                'score': score,
                'metadata': self.metadata[id]['metadata']
            })
        
        return results
    
    def _cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        a_np = np.array(a)
        b_np = np.array(b)
        return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    
    def persist(self):
        """Persist to disk."""
        import pickle
        with open(self.persist_path / 'vectors.pkl', 'wb') as f:
            pickle.dump({'vectors': self.vectors, 'metadata': self.metadata}, f)
    
    def load(self, path=None):
        """Load from disk."""
        import pickle
        load_path = path or self.persist_path
        with open(load_path / 'vectors.pkl', 'rb') as f:
            data = pickle.load(f)
            self.vectors = data['vectors']
            self.metadata = data['metadata']
        return self
```

## 🔄 Integration

Module này được sử dụng bởi:
- `src/retriever/` - Vector similarity search
- `src/pipelines/` - Document indexing and retrieval
- `src/rag/` - Context retrieval for generation

## 📝 Best Practices

1. **Dimension Validation**: Always validate embedding dimensions
2. **Batch Processing**: Use batches cho large datasets
3. **Persistence**: Regularly persist vector store to disk
4. **Memory Management**: Monitor memory usage với large vector stores
5. **Error Handling**: Implement robust error handling cho I/O operations

## 🔍 Troubleshooting

### Common Issues

1. **Dimension Mismatch**: Check embedding model dimensions (384 vs 768)
2. **Memory Issues**: Use smaller batch sizes hoặc chunk processing
3. **Slow Search**: Optimize ChromaDB indexing và consider hardware
4. **Corrupted Store**: Implement backup và recovery procedures

### Debug Tools

```python
# Vector store diagnostics
class VectorStoreDiagnostics:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
    
    def diagnose(self):
        """Run comprehensive diagnostics."""
        collection = self.vectorstore._get_collection()
        
        print(f"Collection name: {self.vectorstore.collection_name}")
        print(f"Document count: {collection.count()}")
        print(f"Embedding dimension: {self.vectorstore.embedding_dimension}")
        
        # Test search
        test_embedding = [0.0] * self.vectorstore.embedding_dimension
        try:
            results = self.vectorstore.similarity_search(test_embedding, top_k=1)
            print(f"Search test: PASSED ({len(results)} results)")
        except Exception as e:
            print(f"Search test: FAILED ({e})")
        
        # Test persistence
        try:
            self.vectorstore.persist()
            print("Persistence test: PASSED")
        except Exception as e:
            print(f"Persistence test: FAILED ({e})")
```

## 📋 TODO

- [ ] Add support for additional vector stores (FAISS, Pinecone, Weaviate)
- [ ] Implement vector store migration tools
- [ ] Add vector store monitoring và metrics
- [ ] Support for vector store sharding
- [ ] Implement incremental updates
- [ ] Add vector store compression
- [ ] Support for hybrid search (vector + keyword)
- [ ] Add vector store backup automation
