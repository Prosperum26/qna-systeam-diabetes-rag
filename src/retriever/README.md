# Vector Retriever Module

Module này cung cấp các implementations cho việc retrieving relevant document chunks dựa trên user queries, sử dụng vector similarity search để tìm kiếm nội dung phù hợp nhất cho hệ thống RAG.

## 🎯 Mục tiêu

- Tìm kiếm các document chunks relevant nhất dựa trên user query
- Hỗ trợ multiple retrieval strategies (vector similarity, hybrid search)
- Optimize retrieval performance và accuracy
- Cung cấp flexible interface cho different vector stores
- Support advanced retrieval features (filtering, re-ranking)

## 🏗️ Kiến trúc

```
src/retriever/
├── __init__.py
├── base.py              # Abstract base class for retrievers
├── vector_retriever.py   # Vector-based similarity search
└── README.md           # This file
```

## 🔧 Components

### BaseRetriever (`base.py`)

Abstract base class định nghĩa interface cho tất cả retrievers:

```python
class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for given query.
        
        Returns:
            List of chunks with at minimum:
            - "text": The chunk content
            - "score": Similarity score (optional)
            - "source": Source document (optional)
            - "chunk_id": Unique chunk identifier (optional)
        """
```

### VectorRetriever (`vector_retriever.py`)

Implementation cho vector-based similarity search:

```python
class VectorRetriever(BaseRetriever):
    def __init__(self, vectorstore, embedder, top_k: int = 5):
        self.vectorstore = vectorstore
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Complete retrieval pipeline:
        1. Clean query text
        2. Embed query vector
        3. Search vector store
        4. Return top-k results
        """
```

**Pipeline Flow:**
1. **Query Cleaning**: Normalize và preprocess query
2. **Query Embedding**: Convert text to vector representation
3. **Vector Search**: Find similar vectors trong store
4. **Result Formatting**: Return structured results with scores

## 🚀 Usage

### Basic Vector Retrieval

```python
from src.retriever.vector_retriever import VectorRetriever
from src.embedder import Embedder
from src.vectorstore import ChromaVectorStore

# Initialize components
embedder = Embedder()
vectorstore = ChromaVectorStore("data/vectorstore")

# Create retriever
retriever = VectorRetriever(
    vectorstore=vectorstore,
    embedder=embedder,
    top_k=5
)

# Retrieve relevant chunks
query = "What are the symptoms of diabetes?"
results = retriever.retrieve(query)

for i, result in enumerate(results, 1):
    print(f"Result {i}:")
    print(f"Score: {result.get('score', 'N/A')}")
    print(f"Text: {result.get('text', '')[:100]}...")
    print(f"Source: {result.get('source', 'Unknown')}")
    print("---")
```

### Advanced Retrieval with Custom Settings

```python
# High-precision retrieval
precision_retriever = VectorRetriever(
    vectorstore=vectorstore,
    embedder=Embedder(model_name="paraphrase-mpnet-base-v2"),
    top_k=3
)

# Broad retrieval with more results
broad_retriever = VectorRetriever(
    vectorstore=vectorstore,
    embedder=embedder,
    top_k=10
)
```

### Integration with RAG Pipeline

```python
from src.retriever.vector_retriever import VectorRetriever

class RAGPipeline:
    def __init__(self):
        self.retriever = VectorRetriever(vectorstore, embedder, top_k=5)
        self.llm = RAGGenerator()
    
    def ask(self, question: str) -> str:
        # Retrieve relevant chunks
        chunks = self.retriever.retrieve(question)
        
        # Generate answer
        context = "\n\n".join([chunk['text'] for chunk in chunks])
        answer = self.llm.generate(question, context)
        
        return answer
```

## 📊 Retrieval Process

### Query Processing

```python
def retrieve(self, query: str) -> List[Dict[str, Any]]:
    # Step 1: Clean and normalize query
    clean_q = clean_query(query)
    
    # Step 2: Generate query embedding
    query_embedding = self.embedder.embed(clean_q)
    
    # Step 3: Search vector store
    results = self.vectorstore.similarity_search(
        query_embedding,
        top_k=self.top_k
    )
    
    # Step 4: Return formatted results
    return results
```

### Result Format

```python
results = [
    {
        "text": "Type 2 diabetes is characterized by insulin resistance...",
        "score": 0.89,
        "source": "Diabetes Overview",
        "chunk_id": "doc_001_chunk_2",
        "metadata": {
            "heading": "Types of Diabetes",
            "doc_id": "doc_001"
        }
    },
    {
        "text": "Common symptoms include increased thirst and frequent urination...",
        "score": 0.85,
        "source": "Diabetes Symptoms",
        "chunk_id": "doc_003_chunk_1",
        "metadata": {
            "heading": "Early Symptoms",
            "doc_id": "doc_003"
        }
    }
]
```

## ⚙️ Configuration

### Retrieval Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vectorstore` | VectorStore | Required | Vector database instance |
| `embedder` | Embedder | Required | Text embedding model |
| `top_k` | int | 5 | Number of chunks to retrieve |

### Performance Tuning

```python
# For faster retrieval
fast_retriever = VectorRetriever(
    vectorstore=vectorstore,
    embedder=Embedder(model_name="all-MiniLM-L6-v2"),  # Faster embedding
    top_k=3  # Fewer results
)

# For higher quality
quality_retriever = VectorRetriever(
    vectorstore=vectorstore,
    embedder=Embedder(model_name="paraphrase-mpnet-base-v2"),  # Better embedding
    top_k=10  # More results
)
```

## 🔍 Advanced Features

### Custom Retrieval Strategies

```python
class HybridRetriever(BaseRetriever):
    """Hybrid retrieval combining semantic and keyword search."""
    
    def __init__(self, vectorstore, embedder, keyword_index, top_k: int = 5):
        self.vector_retriever = VectorRetriever(vectorstore, embedder, top_k)
        self.keyword_index = keyword_index
        self.top_k = top_k
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # Semantic search
        semantic_results = self.vector_retriever.retrieve(query)
        
        # Keyword search
        keyword_results = self.keyword_index.search(query, top_k=self.top_k)
        
        # Combine and re-rank
        all_results = semantic_results + keyword_results
        return self._rerank_results(query, all_results)[:self.top_k]
    
    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Re-rank results based on multiple factors."""
        for result in results:
            # Calculate combined score
            semantic_score = result.get('score', 0)
            keyword_score = self._calculate_keyword_score(query, result['text'])
            result['combined_score'] = 0.7 * semantic_score + 0.3 * keyword_score
        
        return sorted(results, key=lambda x: x.get('combined_score', 0), reverse=True)
```

### Filtered Retrieval

```python
class FilteredRetriever(VectorRetriever):
    """Retriever with metadata filtering capabilities."""
    
    def retrieve(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """
        Retrieve with optional filters.
        
        Args:
            query: Search query
            filters: Dict of filters, e.g., {"category": "diabetes", "date": "2024"}
        """
        # Standard retrieval
        results = super().retrieve(query)
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        return results
    
    def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """Apply metadata filters to results."""
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
        
        return filtered_results
```

### Query Expansion

```python
class QueryExpansionRetriever(VectorRetriever):
    """Retriever with automatic query expansion."""
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # Expand query with synonyms and related terms
        expanded_queries = self._expand_query(query)
        
        # Retrieve for all query variations
        all_results = []
        for expanded_query in expanded_queries:
            results = super().retrieve(expanded_query)
            all_results.extend(results)
        
        # Deduplicate and re-rank
        unique_results = self._deduplicate_results(all_results)
        return self._rerank_by_relevance(query, unique_results)[:self.top_k]
    
    def _expand_query(self, query: str) -> List[str]:
        """Generate query variations."""
        # Medical term expansion
        medical_synonyms = {
            "diabetes": ["diabetes mellitus", "high blood sugar"],
            "symptoms": ["signs", "indications", "manifestations"],
            "treatment": ["therapy", "management", "care"]
        }
        
        expanded = [query]
        for term, synonyms in medical_synonyms.items():
            if term.lower() in query.lower():
                for synonym in synonyms:
                    expanded.append(query.replace(term, synonym, 1))
        
        return list(set(expanded))  # Remove duplicates
```

## 🧪 Testing

```bash
# Run retriever tests
python -m pytest tests/test_retriever.py

# Test with sample data
python -c "
from src.retriever.vector_retriever import VectorRetriever
from src.embedder import Embedder
from src.vectorstore import ChromaVectorStore

retriever = VectorRetriever(
    ChromaVectorStore('data/vectorstore'),
    Embedder(),
    top_k=3
)

results = retriever.retrieve('What is diabetes?')
print(f'Retrieved {len(results)} chunks')
for r in results:
    print(f'Score: {r.get(\"score\", \"N/A\")} - {r.get(\"text\", \"\")[:50]}...')
"
```

### Performance Benchmarking

```python
import time
from src.retriever.vector_retriever import VectorRetriever

def benchmark_retrieval(retriever, queries):
    """Benchmark retrieval performance."""
    times = []
    for query in queries:
        start_time = time.time()
        results = retriever.retrieve(query)
        end_time = time.time()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    print(f"Average retrieval time: {avg_time:.3f}s")
    return times

# Usage
queries = [
    "diabetes symptoms",
    "treatment options",
    "prevention methods"
]
benchmark_retrieval(retriever, queries)
```

## 🔧 Customization

### Custom Scoring Functions

```python
class CustomScoringRetriever(VectorRetriever):
    """Retriever with custom scoring logic."""
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        results = super().retrieve(query)
        
        # Apply custom scoring
        for result in results:
            base_score = result.get('score', 0)
            
            # Boost recent documents
            recency_boost = self._calculate_recency_boost(result)
            
            # Boost authoritative sources
            authority_boost = self._calculate_authority_boost(result)
            
            # Calculate final score
            result['custom_score'] = (
                0.6 * base_score +
                0.2 * recency_boost +
                0.2 * authority_boost
            )
        
        # Sort by custom score
        results.sort(key=lambda x: x.get('custom_score', 0), reverse=True)
        return results
```

### Domain-Specific Retrieval

```python
class MedicalRetriever(VectorRetriever):
    """Medical domain-specific retriever."""
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # Detect query type
        query_type = self._classify_medical_query(query)
        
        # Adjust retrieval based on query type
        if query_type == "symptoms":
            return self._retrieve_symptoms(query)
        elif query_type == "treatment":
            return self._retrieve_treatment(query)
        else:
            return super().retrieve(query)
    
    def _classify_medical_query(self, query: str) -> str:
        """Classify medical query type."""
        symptom_keywords = ["symptom", "sign", "feel", "experience"]
        treatment_keywords = ["treatment", "therapy", "medication", "cure"]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in symptom_keywords):
            return "symptoms"
        elif any(keyword in query_lower for keyword in treatment_keywords):
            return "treatment"
        else:
            return "general"
```

## 🔄 Integration

Module này được sử dụng bởi:
- `src/rag/pipeline.py` - Core RAG operations
- `src/pipelines/chat_pipeline.py` - End-to-end chat pipeline
- `src/llm/` - Context building for generation

## 📝 Best Practices

1. **Query Optimization**: Clean và normalize queries cho better retrieval
2. **Result Quality**: Monitor relevance scores và adjust parameters
3. **Performance**: Optimize embedding và search operations
4. **Filtering**: Use metadata filters cho domain-specific retrieval
5. **Logging**: Monitor retrieval patterns và performance

## 🔍 Troubleshooting

### Common Issues

1. **Poor Retrieval Quality**: Check embedding model và vector store quality
2. **Slow Performance**: Optimize vector store indexing và query processing
3. **No Results**: Verify query processing và vector store connectivity
4. **Inconsistent Scores**: Check normalization và similarity calculations

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect retrieval process
class DebugRetriever(VectorRetriever):
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        print(f"Original query: {query}")
        
        # Debug query cleaning
        clean_q = clean_query(query)
        print(f"Cleaned query: {clean_q}")
        
        # Debug embedding
        query_embedding = self.embedder.embed(clean_q)
        print(f"Query embedding shape: {len(query_embedding)}")
        
        # Debug search
        results = super().retrieve(query)
        print(f"Retrieved {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"Result {i}: score={result.get('score', 0):.3f}")
        
        return results
```

## 📋 TODO

- [ ] Implement hybrid retrieval combining semantic and keyword search
- [ ] Add support for query rewriting và expansion
- [ ] Implement relevance feedback và learning
- [ ] Add support for multi-modal retrieval
- [ ] Implement caching mechanisms
- [ ] Add retrieval quality metrics
- [ ] Support for distributed retrieval
- [ ] Add A/B testing framework for retrieval strategies
