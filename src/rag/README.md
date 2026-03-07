# RAG Pipeline Module

Module này cung cấp implementation cho Retrieval-Augmented Generation (RAG) pipeline, kết hợp vector retrieval và LLM generation để tạo ra câu trả lời chính xác dựa trên kiến thức đã có.

## 🎯 Mục tiêu

- Orchestrate toàn bộ RAG flow từ query đến response
- Kết hợp retrieval và generation một cách hiệu quả
- Tối ưu context building cho best possible answers
- Cung cấp interface đơn giản cho RAG operations
- Support advanced RAG techniques và optimizations

## 🏗️ Kiến trúc

```
src/rag/
├── __init__.py
├── pipeline.py         # Core RAG pipeline implementation
└── README.md          # This file
```

## 🔧 Components

### RAGPipeline (`pipeline.py`)

Core pipeline class orchestrates entire RAG process:

```python
class RAGPipeline:
    def __init__(self, embedder, vectorstore, llm, top_k: int = 5):
        self.embedder = embedder
        self.vectorstore = vectorstore
        self.llm = llm
        self.top_k = top_k

    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """
        Complete RAG flow:
        1. Embed question
        2. Retrieve relevant chunks
        3. Build context prompt
        4. Generate answer
        5. Return response
        """
```

**Pipeline Flow:**
1. **Query Processing**: Embed user query
2. **Vector Retrieval**: Search vector store for relevant chunks
3. **Context Building**: Format retrieved chunks into prompt
4. **Answer Generation**: LLM generates response based on context
5. **Response Formatting**: Return structured answer

## 🚀 Usage

### Basic RAG Pipeline

```python
from src.rag.pipeline import RAGPipeline
from src.embedder import Embedder
from src.vectorstore import ChromaVectorStore
from src.llm import RAGGenerator

# Initialize components
embedder = Embedder()
vectorstore = ChromaVectorStore("data/vectorstore")
llm = RAGGenerator()

# Create pipeline
pipeline = RAGPipeline(
    embedder=embedder,
    vectorstore=vectorstore,
    llm=llm,
    top_k=5
)

# Ask question
answer = pipeline.ask("What are the symptoms of diabetes?")
print(answer)
```

### Advanced Pipeline with Custom Configuration

```python
# Pipeline with custom settings
pipeline = RAGPipeline(
    embedder=Embedder(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
    vectorstore=ChromaVectorStore("data/vectorstore"),
    llm=RAGGenerator(model="llama3", temperature=0.2),
    top_k=10
)

# Ask with custom system prompt
system_prompt = "You are a medical assistant specializing in diabetes care."
answer = pipeline.ask(
    question="How is type 2 diabetes diagnosed?",
    system_prompt=system_prompt
)
```

### Pipeline with Error Handling

```python
def safe_ask(pipeline, question, max_retries=3):
    """Ask question with retry logic."""
    for attempt in range(max_retries):
        try:
            answer = pipeline.ask(question)
            return answer
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return "I apologize, but I'm unable to answer that question right now."
    return None

# Usage
answer = safe_ask(pipeline, "What is diabetes?")
```

## 📊 Pipeline Architecture

### Data Flow

```
User Question → Query Embedding → Vector Search → Retrieved Chunks
     ↓
Context Building → Prompt Construction → LLM Generation → Final Answer
```

### Component Interactions

```python
class RAGPipeline:
    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        # 1. Query Embedding
        query_embedding = self.embedder.embed(question)
        
        # 2. Vector Retrieval
        retrieved_chunks = self.vectorstore.search(
            query_embedding, 
            top_k=self.top_k
        )
        
        # 3. Context Building
        context = self.build_context(retrieved_chunks)
        
        # 4. Answer Generation
        answer = self.llm.generate_answer(
            question=question,
            context=context,
            system_prompt=system_prompt
        )
        
        return answer
```

## ⚙️ Configuration

### Pipeline Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `embedder` | Embedder | Required | Text embedding model |
| `vectorstore` | VectorStore | Required | Vector database |
| `llm` | LLM | Required | Language model |
| `top_k` | int | 5 | Number of chunks to retrieve |

### Performance Tuning

```python
# For faster responses
fast_pipeline = RAGPipeline(
    embedder=Embedder(model_name="all-MiniLM-L6-v2"),  # Faster embedding
    vectorstore=vectorstore,
    llm=RAGGenerator(temperature=0.1),  # More deterministic
    top_k=3  # Fewer chunks
)

# For higher quality
quality_pipeline = RAGPipeline(
    embedder=Embedder(model_name="paraphrase-mpnet-base-v2"),  # Better embeddings
    vectorstore=vectorstore,
    llm=RAGGenerator(temperature=0.2),
    top_k=10  # More context
)
```

## 🔍 Advanced Features

### Context Building Strategies

```python
class AdvancedRAGPipeline(RAGPipeline):
    def build_context(self, chunks):
        """Advanced context building with relevance scoring."""
        # Sort by relevance score
        sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
        
        # Build context with metadata
        context_parts = []
        for i, chunk in enumerate(sorted_chunks, 1):
            context_parts.append(
                f"[Source {i}: {chunk.get('title', 'Unknown')} - {chunk.get('heading', 'Section')}]\n"
                f"{chunk.get('content', '')}"
            )
        
        return "\n\n".join(context_parts)
    
    def ask(self, question: str, system_prompt: Optional[str] = None) -> dict:
        """Enhanced ask with metadata."""
        # Standard pipeline
        answer = super().ask(question, system_prompt)
        
        # Return enhanced response
        return {
            "answer": answer,
            "sources": [chunk.get('title') for chunk in self.last_retrieved_chunks],
            "context_length": len(self.last_context),
            "retrieval_time": self.retrieval_time,
            "generation_time": self.generation_time
        }
```

### Multi-Query RAG

```python
class MultiQueryRAGPipeline(RAGPipeline):
    def ask(self, question: str, system_prompt: Optional[str] = None) -> str:
        """Generate multiple query variants for better retrieval."""
        # Generate query variations
        query_variations = self.generate_query_variants(question)
        
        # Retrieve chunks for all queries
        all_chunks = []
        for query in query_variations:
            chunks = self.vectorstore.search(
                self.embedder.embed(query),
                top_k=self.top_k
            )
            all_chunks.extend(chunks)
        
        # Deduplicate and re-rank
        unique_chunks = self.deduplicate_chunks(all_chunks)
        ranked_chunks = self.rerank_chunks(question, unique_chunks)
        
        # Generate answer
        context = self.build_context(ranked_chunks[:self.top_k])
        return self.llm.generate_answer(question, context, system_prompt)
```

## 🧪 Testing

```bash
# Run RAG pipeline tests
python -m pytest tests/test_rag_pipeline.py

# Test with sample data
python -c "
from src.rag.pipeline import RAGPipeline
# Initialize with mock components for testing
pipeline = RAGPipeline(mock_embedder, mock_vectorstore, mock_llm)
answer = pipeline.ask('What is diabetes?')
print(answer)
"

# Integration test
python -c "
from src.rag.pipeline import RAGPipeline
from src.embedder import Embedder
from src.vectorstore import ChromaVectorStore
from src.llm import RAGGenerator

# Real integration test
pipeline = RAGPipeline(Embedder(), ChromaVectorStore(), RAGGenerator())
answer = pipeline.ask('What are diabetes symptoms?')
print(f'Answer: {answer}')
"
```

### Performance Benchmarking

```python
import time
from src.rag.pipeline import RAGPipeline

def benchmark_pipeline(pipeline, questions):
    """Benchmark pipeline performance."""
    times = []
    for question in questions:
        start_time = time.time()
        answer = pipeline.ask(question)
        end_time = time.time()
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Min: {min(times):.2f}s, Max: {max(times):.2f}s")
    return times

# Usage
questions = [
    "What is diabetes?",
    "How is diabetes treated?",
    "What are the complications?"
]
benchmark_pipeline(pipeline, questions)
```

## 🔧 Customization

### Custom Context Builders

```python
class MedicalRAGPipeline(RAGPipeline):
    def build_context(self, chunks):
        """Medical-specific context building."""
        # Filter for medical relevance
        medical_chunks = [c for c in chunks if self.is_medical_content(c)]
        
        # Prioritize recent information
        recent_chunks = sorted(
            medical_chunks,
            key=lambda x: x.get('date', ''),
            reverse=True
        )
        
        # Add medical disclaimer
        context = "MEDICAL INFORMATION (for educational purposes only):\n\n"
        for chunk in recent_chunks:
            context += f"{chunk.get('content', '')}\n\n"
        
        context += "\nNote: This information is not a substitute for professional medical advice."
        return context
    
    def is_medical_content(self, chunk):
        """Check if chunk contains medical information."""
        medical_keywords = ['diabetes', 'blood sugar', 'insulin', 'glucose', 'treatment']
        content = chunk.get('content', '').lower()
        return any(keyword in content for keyword in medical_keywords)
```

### Custom Retrieval Strategies

```python
class HybridRAGPipeline(RAGPipeline):
    def retrieve_chunks(self, question):
        """Hybrid retrieval combining semantic and keyword search."""
        # Semantic search
        semantic_chunks = self.vectorstore.search(
            self.embedder.embed(question),
            top_k=self.top_k
        )
        
        # Keyword search (if supported)
        keyword_chunks = self.vectorstore.keyword_search(
            question,
            top_k=self.top_k
        )
        
        # Combine and re-rank
        all_chunks = semantic_chunks + keyword_chunks
        return self.rerank_chunks(question, all_chunks)[:self.top_k]
```

## 🔄 Integration

Module này tích hợp các components khác:
- `src/embedder/` - Query embedding
- `src/vectorstore/` - Vector retrieval
- `src/llm/` - Answer generation
- `src/retriever/` - Advanced retrieval logic

## 📝 Best Practices

1. **Context Quality**: Ensure retrieved chunks are relevant and high-quality
2. **Token Management**: Monitor context length to avoid model limits
3. **Answer Quality**: Validate answers against source material
4. **Performance**: Optimize retrieval and generation speed
5. **Error Handling**: Implement graceful fallbacks

## 🔍 Troubleshooting

### Common Issues

1. **Poor Retrieval**: Check embedding model and vector store quality
2. **Long Responses**: Reduce context size or adjust generation parameters
3. **Irrelevant Answers**: Improve retrieval relevance and context building
4. **Slow Performance**: Optimize embedding and retrieval operations

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect intermediate steps
class DebugRAGPipeline(RAGPipeline):
    def ask(self, question, system_prompt=None):
        print(f"Question: {question}")
        
        # Debug embedding
        query_embedding = self.embedder.embed(question)
        print(f"Query embedding shape: {query_embedding.shape}")
        
        # Debug retrieval
        chunks = self.vectorstore.search(query_embedding, top_k=self.top_k)
        print(f"Retrieved {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk.get('title', 'Unknown')} - score: {chunk.get('score', 0):.3f}")
        
        # Debug generation
        answer = super().ask(question, system_prompt)
        print(f"Answer length: {len(answer)} characters")
        
        return answer
```

## 📋 TODO

- [ ] Implement complete pipeline logic trong `pipeline.py`
- [ ] Add support for conversation memory
- [ ] Implement query rewriting và expansion
- [ ] Add answer quality scoring
- [ ] Support for multi-modal RAG
- [ ] Implement caching mechanisms
- [ ] Add A/B testing framework
- [ ] Support for streaming responses
