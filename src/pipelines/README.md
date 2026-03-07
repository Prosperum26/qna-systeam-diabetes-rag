# Chat Pipeline Module

Module này cung cấp pipeline hoàn chỉnh cho hệ thống RAG chatbot, kết nối tất cả các thành phần từ vector retrieval đến LLM generation để tạo ra một hệ thống hỏi đáp thông minh.

## 🎯 Mục tiêu

- Tích hợp tất cả modules thành một pipeline hoàn chỉnh
- Cung cấp interface đơn giản cho end-to-end RAG operations
- Hỗ trợ cả programmatic API và CLI interface
- Optimize performance với caching và batch processing
- Provide comprehensive logging và monitoring

## 🏗️ Kiến trúc

```
src/pipelines/
├── chat_pipeline.py    # Main RAG pipeline implementation
└── README.md          # This file
```

## 🔧 Components

### RAGChatPipeline (`chat_pipeline.py`)

Core pipeline class orchestrates entire RAG flow:

```python
class RAGChatPipeline:
    def __init__(
        self,
        vectorstore_path: str = "data/vectorstore",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        top_k: int = 5,
        max_context_tokens: int = 1500,
        temperature: float = 0.2
    )
```

**Pipeline Flow:**
1. User Query → Vector Embedding
2. Vector Similarity Search → Relevant Chunks
3. Context Building → LLM Generation
4. Response Formatting → Final Answer

## 🚀 Usage

### Programmatic API

```python
from src.pipelines.chat_pipeline import RAGChatPipeline

# Initialize pipeline
pipeline = RAGChatPipeline(
    vectorstore_path="data/vectorstore",
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    llm_model="llama3",
    top_k=5,
    max_context_tokens=1500
)

# Simple query
response = pipeline.query("What are the symptoms of diabetes?")
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")

# Batch queries
queries = [
    "What is type 1 diabetes?",
    "How is diabetes diagnosed?",
    "What are the treatment options?"
]
responses = pipeline.batch_query(queries)
for query, resp in zip(queries, responses):
    print(f"Q: {query}")
    print(f"A: {resp.answer}")
    print("---")
```

### CLI Interface

```bash
# Interactive chat mode
python -m src.pipelines.chat_pipeline chat

# Single query
python -m src.pipelines.chat_pipeline query "What is diabetes?"

# Batch queries from file
python -m src.pipelines.chat_pipeline batch --file queries.txt

# Health check
python -m src.pipelines.chat_pipeline health
```

### Advanced Usage

```python
# Custom pipeline with specific configuration
pipeline = RAGChatPipeline(
    vectorstore_path="custom_vectorstore",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    llm_model="llama3:instruct",
    top_k=10,
    max_context_tokens=2000,
    temperature=0.1
)

# Query with custom options
response = pipeline.query(
    query="Explain diabetes complications",
    include_metadata=True,
    min_relevance_score=0.7
)

# Get detailed statistics
stats = pipeline.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Average response time: {stats['avg_response_time']:.2f}s")
```

## 📊 Configuration

### Pipeline Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `vectorstore_path` | "data/vectorstore" | Path to ChromaDB |
| `embedding_model` | paraphrase-multilingual-MiniLM-L12-v2 | Embedding model |
| `llm_model` | "llama3" | Ollama model name |
| `ollama_base_url` | "http://localhost:11434" | Ollama server |
| `top_k` | 5 | Number of chunks to retrieve |
| `max_context_tokens` | 1500 | Maximum context for LLM |
| `temperature` | 0.2 | LLM sampling temperature |

### Performance Tuning

```python
# For faster responses
fast_pipeline = RAGChatPipeline(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Faster model
    top_k=3,  # Fewer chunks
    max_context_tokens=800  # Smaller context
)

# For higher quality
quality_pipeline = RAGChatPipeline(
    top_k=10,  # More chunks
    max_context_tokens=2000,  # Larger context
    temperature=0.1  # More deterministic
)
```

## 🔍 Response Format

### RAGResponse Structure

```python
@dataclass
class RAGResponse:
    answer: str              # Generated answer
    sources: List[str]       # Source document titles
    chunk_count: int         # Number of chunks used
    context_tokens: int      # Estimated token count
    query_time: float        # Time taken for query
    retrieval_time: float    # Time for retrieval
    generation_time: float   # Time for generation
    chunks_used: List[Dict]  # Actual chunks used (optional)
```

### Example Response

```python
response = pipeline.query("What is diabetes?")

print(f"Answer: {response.answer}")
# Answer: Diabetes is a chronic disease that affects how your body processes glucose...

print(f"Sources: {response.sources}")
# Sources: ['Diabetes Overview', 'Understanding Type 2 Diabetes']

print(f"Used {response.chunk_count} chunks in {response.query_time:.2f}s")
# Used 3 chunks in 1.23s
```

## 📈 Performance Metrics

### Typical Performance

| Operation | Average Time | Notes |
|-----------|--------------|-------|
| Query embedding | ~50ms | CPU, ~10ms GPU |
| Vector search | ~100ms | 10k chunks |
| Context building | ~20ms | 5 chunks |
| LLM generation | ~2-5s | Depends on model |
| **Total** | **~2.5-6s** | End-to-end |

### Monitoring

```python
# Enable performance monitoring
pipeline.enable_monitoring()

# Query multiple times
for _ in range(10):
    pipeline.query("What is diabetes?")

# Get performance stats
stats = pipeline.get_performance_stats()
print(f"Average query time: {stats['avg_query_time']:.2f}s")
print(f"P95 query time: {stats['p95_query_time']:.2f}s")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
```

## 🧪 Testing

```bash
# Run pipeline tests
python -m pytest tests/test_chat_pipeline.py

# Test with sample data
python -c "
from src.pipelines.chat_pipeline import RAGChatPipeline
pipeline = RAGChatPipeline()
response = pipeline.query('What is diabetes?')
print(response.answer)
"

# Performance benchmark
python -m src.pipelines.chat_pipeline benchmark --queries 100
```

### Unit Test Examples

```python
def test_pipeline_initialization():
    pipeline = RAGChatPipeline()
    assert pipeline.vectorstore is not None
    assert pipeline.retriever is not None
    assert pipeline.generator is not None

def test_simple_query():
    pipeline = RAGChatPipeline()
    response = pipeline.query("What is diabetes?")
    assert response.answer is not None
    assert len(response.sources) > 0
```

## 🔧 Customization

### Custom Retrieval Strategy

```python
class CustomPipeline(RAGChatPipeline):
    def retrieve_chunks(self, query: str) -> List[Dict]:
        # Custom retrieval logic
        chunks = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
            filters={"category": "diabetes"}
        )
        
        # Custom relevance scoring
        scored_chunks = []
        for chunk in chunks:
            score = self.calculate_relevance_score(query, chunk)
            if score > 0.7:
                scored_chunks.append(chunk)
        
        return scored_chunks
    
    def calculate_relevance_score(self, query: str, chunk: Dict) -> float:
        # Custom scoring logic
        # Consider semantic similarity, recency, source authority
        return 0.8
```

### Custom Response Processing

```python
class EnhancedPipeline(RAGChatPipeline):
    def process_response(self, response: RAGResponse) -> RAGResponse:
        # Add confidence scores
        response.confidence = self.calculate_confidence(response)
        
        # Add related questions
        response.related_questions = self.generate_related_questions(response)
        
        # Add citations
        response.citations = self.format_citations(response.sources)
        
        return response
```

### Integration with External Systems

```python
# API integration
from flask import Flask, request, jsonify

app = Flask(__name__)
pipeline = RAGChatPipeline()

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    response = pipeline.query(query)
    return jsonify({
        'answer': response.answer,
        'sources': response.sources,
        'metadata': {
            'chunk_count': response.chunk_count,
            'response_time': response.query_time
        }
    })
```

## 🔄 Integration

Module này tích hợp tất cả các modules khác:
- `src/vectorstore/` - Vector database operations
- `src/retriever/` - Similarity search
- `src/llm/` - Text generation
- `src/embedder/` - Query embedding

## 📝 Best Practices

1. **Performance**: Monitor response times và optimize bottlenecks
2. **Quality**: Review retrieved chunks cho relevance
3. **Caching**: Enable query caching cho repeated questions
4. **Monitoring**: Log all queries và responses cho analysis
5. **Error Handling**: Implement graceful degradation

## 🔍 Troubleshooting

### Common Issues

1. **Slow responses**: Check LLM generation time, consider smaller models
2. **Poor answers**: Verify chunk quality và retrieval relevance
3. **Connection errors**: Ensure Ollama is running và accessible
4. **Memory issues**: Monitor vector store size và query complexity

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect intermediate steps
pipeline = RAGChatPipeline()
pipeline.debug_mode = True

response = pipeline.query("What is diabetes?")
# Debug info will show retrieval, context building, generation steps

# Performance profiling
pipeline.profile_query("What is diabetes?")
# Shows timing breakdown for each step
```

## 📋 TODO

- [ ] Add query caching mechanism
- [ ] Implement streaming responses
- [ ] Add conversation memory
- [ ] Support for multiple retrieval strategies
- [ ] Add A/B testing framework
- [ ] Implement query analytics dashboard
- [ ] Add support for multimodal queries
- [ ] Implement response quality scoring
