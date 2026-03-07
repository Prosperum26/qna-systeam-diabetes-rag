# LLM Module for RAG System

This module provides a complete Retrieval-Augmented Generation (RAG) implementation for chatbot systems using Ollama and Llama3.

## Architecture

```
llm/
├── prompt_template.py    # RAG prompt templates with hallucination prevention
├── context_builder.py   # Context building with token budget control
├── llm_client.py        # Ollama API client
├── generator.py         # Main orchestrator with RAGResponse
└── logging_config.py    # Centralized logging configuration
```

## Quick Start

```python
from src.llm import RAGGenerator

# Initialize the generator
generator = RAGGenerator(
    ollama_base_url="http://localhost:11434",
    model="llama3",
    max_context_tokens=1500
)

# Example chunks from retriever
chunks = [
    {
        "chunk_id": "chunk_1",
        "doc_id": "doc_1", 
        "title": "Diabetes Overview",
        "heading": "Introduction",
        "text": "Diabetes is a chronic disease that affects how your body processes glucose...",
        "position": 0,
        "token_count": 45
    }
]

# Generate answer
response = generator.generate_answer(
    query="What is diabetes?",
    chunks=chunks
)

print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")
```

## Components

### RAGGenerator

Main orchestrator that coordinates the entire RAG pipeline:

- **Input**: User query + retrieved chunks
- **Output**: RAGResponse with answer and sources
- **Features**: Token budget control, source attribution, error handling

### ContextBuilder

Converts retrieved chunks into formatted context:

- Preserves metadata (title, heading)
- Implements token budget control
- Uses clear document separators
- Maintains relevance order

### PromptTemplate

Builds RAG prompts that prevent hallucination:

- Forces LLM to use only provided context
- Includes fallback response for unknown answers
- Structured format for optimal parsing

### OllamaClient

HTTP client for Ollama API:

- Configurable model and temperature
- Connection health checking
- Comprehensive error handling
- Timeout management

### RAGResponse

Structured response object:

```python
@dataclass
class RAGResponse:
    answer: str              # Generated answer
    sources: List[str]       # Source document titles/IDs
    chunk_count: int         # Number of chunks used
    context_tokens: int      # Estimated token count
```

## Configuration

### Logging

```python
from src.llm.logging_config import setup_logging

# Setup logging with custom level
setup_logging(level="DEBUG", include_timestamp=True)
```

### Generator Options

```python
generator = RAGGenerator(
    ollama_base_url="http://localhost:11434",  # Ollama server
    model="llama3",                           # Model name
    temperature=0.2,                           # Sampling temperature
    max_context_tokens=1500                   # Context token limit
)
```

## Usage Examples

### Basic RAG Generation

```python
from src.llm import RAGGenerator

generator = RAGGenerator()

response = generator.generate_answer(
    query="What are the symptoms of diabetes?",
    chunks=retrieved_chunks
)

print(response.answer)
print(f"Sources: {', '.join(response.sources)}")
```

### Health Check

```python
# Check system health
health = generator.check_system_health()
print(f"Ollama connected: {health['ollama_connected']}")
print(f"Model: {health['model']}")
```

### Custom Context Building

```python
from src.llm import ContextBuilder

builder = ContextBuilder()
context = builder.build_context(
    chunks=chunks,
    max_tokens=1000
)

# Get statistics
stats = builder.get_context_stats(chunks)
print(f"Total chunks: {stats['chunk_count']}")
print(f"Estimated tokens: {stats['estimated_tokens']}")
```

## Logging

The module includes structured logging for monitoring:

- Query processing
- Chunk statistics
- Token usage
- API requests/responses
- Error conditions

Log levels:
- **INFO**: Normal operation
- **DEBUG**: Detailed debugging
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Error Handling

The system includes comprehensive error handling:

- **Connection errors**: Ollama server unavailable
- **Timeout errors**: Long-running requests
- **API errors**: Invalid responses
- **Parsing errors**: Malformed data

## Performance Considerations

- **Token estimation**: Uses character-based estimation (0.25 tokens/char)
- **Context truncation**: Stops adding chunks when token limit reached
- **Connection reuse**: HTTP sessions for multiple requests
- **Timeout management**: Configurable request timeouts

## Dependencies

- `requests`: HTTP client for Ollama API
- `logging`: Python standard library
- `typing`: Type hints
- `dataclasses`: Response objects

## Requirements

- Python 3.7+
- Ollama server running on localhost:11434
- Llama3 model pulled in Ollama

## Best Practices

1. **Token Management**: Monitor context token usage to prevent overflow
2. **Error Handling**: Always wrap generation calls in try/catch
3. **Logging**: Enable DEBUG logging during development
4. **Source Attribution**: Always include sources in responses
5. **Temperature**: Use low temperature (0.1-0.3) for factual responses
