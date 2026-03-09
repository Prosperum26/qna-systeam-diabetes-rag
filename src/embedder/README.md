# Text Embedding Module

Module này chịu trách nhiệm chuyển đổi văn bản thành vector embeddings sử dụng pre-trained transformer models, cho phép tìm kiếm tương đồng và retrieval trong hệ thống RAG.

## 🎯 Mục tiêu

- Chuyển đổi text chunks thành high-quality vector embeddings
- Hỗ trợ multiple embedding models cho different use cases
- Tối ưu performance với batch processing và GPU acceleration
- Normalize vectors cho cosine similarity calculations
- Preserve metadata trong embedded chunks

## 🏗️ Kiến trúc

```
src/embedder/
├── __init__.py
├── embedder.py         # Core embedding class
├── embed_chunks.py     # Batch processing pipeline
└── README.md          # This file
```

## 🔧 Components

### Embedder (`embedder.py`)

Core class cho text embedding:

```python
class Embedder:
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device: str = "cpu",
        normalize: bool = True,
    )
```

**Features:**
- Hỗ trợ multiple sentence-transformer models
- Automatic device selection (CPU/GPU)
- L2 normalization cho cosine similarity
- Batch embedding cho efficiency
- Multilingual support (English/Vietnamese)

### Batch Processing (`embed_chunks.py`)

Pipeline cho processing large chunk collections:

```python
def embed_chunks_pipeline(
    input_path: Path,
    output_path: Path,
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    batch_size: int = 32,
    device: str = "cpu"
)
```

**Features:**
- Load chunks từ JSONL files
- Progress tracking với tqdm
- Batch processing cho memory efficiency
- Error handling và logging
- Save embedded chunks với metadata

## 🚀 Usage

### Single Text Embedding

```python
from src.embedder.embedder import Embedder

# Initialize embedder
embedder = Embedder(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device="cpu",
    normalize=True
)

# Embed single text
text = "Type 2 diabetes is characterized by insulin resistance"
embedding = embedder.embed(text)
print(f"Embedding shape: {embedding.shape}")  # (384,)

# Embed batch
texts = [
    "Diabetes symptoms include increased thirst",
    "Treatment involves lifestyle changes and medication"
]
embeddings = embedder.embed_batch(texts)
print(f"Batch embeddings shape: {embeddings.shape}")  # (2, 384)
```

### Batch Processing Pipeline

```python
from src.embedder.embed_chunks import embed_chunks_pipeline
from pathlib import Path

# Process all chunks
embed_chunks_pipeline(
    input_path=Path("data/processed/chunked.jsonl"),
    output_path=Path("data/processed/embedded_chunks.jsonl"),
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    batch_size=32,
    device="cpu"
)
```

### Custom Processing

```python
from src.embedder.embed_chunks import load_chunks, save_embedded_chunks
from src.embedder.embedder import Embedder

# Load chunks
chunks = load_chunks(Path("data/processed/chunked.jsonl"))

# Initialize embedder
embedder = Embedder()

# Process chunks
embedded_chunks = []
for chunk in chunks:
    text = chunk.get("content", "")
    if text.strip():
        embedding = embedder.embed(text)
        chunk["embedding"] = embedding.tolist()
        embedded_chunks.append(chunk)

# Save results
save_embedded_chunks(embedded_chunks, Path("output/embedded.jsonl"))
```

## 📊 Supported Models

### Recommended Models

| Model | Dimensions | Language | Use Case |
|-------|------------|----------|----------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Multi | Default choice, fast |
| `all-MiniLM-L6-v2` | 384 | English | English-only, faster |
| `paraphrase-mpnet-base-v2` | 768 | English | Higher quality |
| `distiluse-base-multilingual-cased-v1` | 512 | Multi | Balanced quality/speed |

### Model Selection

```python
# For Vietnamese medical content
embedder = Embedder(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# For English-only content
embedder = Embedder(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# For higher quality (slower)
embedder = Embedder(
    model_name="sentence-transformers/paraphrase-mpnet-base-v2"
)
```

## ⚙️ Configuration

### Embedder Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_name` | `paraphrase-multilingual-MiniLM-L12-v2` | HuggingFace model ID |
| `device` | "cpu" | Computation device ("cpu" or "cuda") |
| `normalize` | True | Apply L2 normalization |
| `batch_size` | 32 | Batch size for processing |

### Performance Tuning

```python
# For GPU acceleration
embedder = Embedder(device="cuda")

# For memory-constrained environments
embedder = Embedder(batch_size=16)

# For faster processing (lower quality)
embedder = Embedder(model_name="all-MiniLM-L6-v2")
```

## 📈 Performance Metrics

### Typical Performance

| Model | Dimensions | Speed (CPU) | Speed (GPU) | Quality |
|-------|------------|-------------|-------------|---------|
| MiniLM-L12 | 384 | ~100 docs/s | ~500 docs/s | Good |
| MiniLM-L6 | 384 | ~150 docs/s | ~800 docs/s | Fair |
| MPNet-Base | 768 | ~50 docs/s | ~300 docs/s | Excellent |

### Memory Usage

- **Model loading**: 200-500MB (model dependent)
- **Batch processing**: `batch_size * dimensions * 4` bytes
- **GPU memory**: Model size + intermediate activations

## 🔍 Data Format

### Input Chunk Format

```json
{
  "chunk_id": "doc_001_chunk_0",
  "doc_id": "doc_001",
  "title": "Diabetes Overview",
  "heading": "Introduction",
  "content": "Type 2 diabetes is a chronic condition...",
  "position": 0,
  "token_count": 45
}
```

### Output Embedded Chunk Format

```json
{
  "chunk_id": "doc_001_chunk_0",
  "doc_id": "doc_001",
  "title": "Diabetes Overview",
  "heading": "Introduction",
  "content": "Type 2 diabetes is a chronic condition...",
  "position": 0,
  "token_count": 45,
  "embedding": [0.1234, -0.5678, ...],
  "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
  "embedding_timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

```bash
# Run embedding tests
python -m pytest tests/test_embedder.py

# Test with sample data
python -c "
from src.embedder.embedder import Embedder
embedder = Embedder()
text = 'Diabetes is a metabolic disorder'
embedding = embedder.embed(text)
print(f'Embedding shape: {embedding.shape}')
"
```

### Benchmark Models

```python
# Compare different models
models = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/all-MiniLM-L6-v2"
]

for model in models:
    embedder = Embedder(model_name=model)
    start_time = time.time()
    embedding = embedder.embed(test_text)
    duration = time.time() - start_time
    print(f"{model}: {duration:.3f}s, {embedding.shape}")
```

## 🔧 Customization

### Custom Embedding Function

```python
class CustomEmbedder(Embedder):
    def embed(self, text: str) -> np.ndarray:
        # Preprocess text
        processed_text = self.preprocess(text)
        
        # Get base embedding
        embedding = super().embed(processed_text)
        
        # Post-process
        return self.postprocess(embedding)
    
    def preprocess(self, text: str) -> str:
        # Custom preprocessing
        return text.lower().strip()
    
    def postprocess(self, embedding: np.ndarray) -> np.ndarray:
        # Custom postprocessing
        return embedding / np.linalg.norm(embedding)
```

### Specialized Models

```python
# Medical-specific models (if available)
medical_embedder = Embedder(
    model_name="medical-embedding-model-name",
    normalize=True
)

# Multilingual medical content
multilingual_embedder = Embedder(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

## 🔄 Integration

Module này được sử dụng bởi:
- `src/pipelines/chat_pipeline.py` - End-to-end processing
- `src/vectorstore/` - Vector storage operations
- `src/retriever/` - Similarity search

## 📝 Best Practices

1. **Model Selection**: Choose model based on language and quality requirements
2. **Batch Processing**: Use batch embedding cho large datasets
3. **Memory Management**: Monitor memory usage với large batches
4. **Normalization**: Always normalize vectors cho cosine similarity
5. **Device Selection**: Use GPU khi available cho better performance

## 🔍 Troubleshooting

### Common Issues

1. **CUDA out of memory**: Reduce batch size hoặc use CPU
2. **Model loading failed**: Check model name và internet connection
3. **Slow performance**: Use smaller model hoặc GPU acceleration
4. **Poor quality**: Try different model optimized cho domain

### Debug Tools

```python
# Check model info
print(f"Model: {embedder.model_name}")
print(f"Device: {embedder.device}")
print(f"Vocabulary size: {len(embedder.tokenizer)}")

# Test embedding
test_embedding = embedder.embed("test")
print(f"Embedding shape: {test_embedding.shape}")
print(f"Embedding norm: {np.linalg.norm(test_embedding)}")

# Benchmark
import time
start_time = time.time()
for _ in range(100):
    embedder.embed("test text")
print(f"Average time: {(time.time() - start_time) / 100:.3f}s")
```

## 📋 TODO

- [ ] Add support for OpenAI embeddings
- [ ] Implement embedding caching
- [ ] Add model quantization cho faster inference
- [ ] Support for embedding comparison và evaluation
- [ ] Add embeddings visualization tools
