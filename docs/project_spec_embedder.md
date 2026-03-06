# Embedding Module Design

## 1. Embedded Chunk Schema

Sau khi chunk được tạo, bước tiếp theo là chuyển text thành vector embedding.

**Schema đề xuất cho mỗi embedded chunk:**

```json
{
  "chunk_id": "...",
  "doc_id": "...",
  "text": "...",
  "embedding": [0.12, -0.33, ...],
  "metadata": {
    "title": "...",
    "heading": "...",
    "position": 2
  }
}
```

**Ghi chú:**

- `embedding` là vector biểu diễn ngữ nghĩa của text
- `metadata` không được đưa vào embedding
- `metadata` dùng cho:
  - Context reconstruction
  - Debugging
  - Ranking

## 2. Embedding Dimension

**Recommended dimension: 384**

**Lý do:**

- Đủ tốt cho semantic search
- Nhẹ
- Tốc độ nhanh
- Phù hợp dataset nhỏ / medium

**Ví dụ model thường dùng:**

- Multilingual MiniLM (384 dims)

## 3. Module Structure

```
src/
├ chunking/
├ embedding/
│  ├ embedder.py
│  └ embed_chunks.py
```

### embedder.py

Wrapper cho embedding model.

```python
class Embedder:
    def embed(self, text: str) -> list[float]:
        ...
```

**Responsibilities:**

- Load embedding model
- Convert text → vector
- Handle batching

### embed_chunks.py

Script pipeline cho embedding.

**Pipeline:**

```
load chunks
  ↓
embed text
  ↓
save vectors
```

**Input:** `chunked.jsonl`

**Output:** `embedded_chunks.jsonl`

## 4. Performance Optimization

Embedding có thể rất chậm nếu dataset lớn. Cần tối ưu bằng các kỹ thuật sau.

### Batch Embedding

Không embed từng chunk. Thay vào đó:

```python
batch_size = 32
```

**Batch embedding giúp:**

- Tận dụng GPU/CPU tốt hơn
- Giảm overhead model inference

### Caching

Nếu chunk đã được embed trước đó: skip

**Điều này giúp:**

- Tránh embed lại dữ liệu cũ
- Tăng tốc pipeline

### Progress Bar

Sử dụng `tqdm` để hiển thị tiến trình embedding.

**Ví dụ:**

```
Embedding chunks:  45%|██████████
```

**Giúp:**

- Biết pipeline đang chạy tới đâu
- Dễ debug khi dataset lớn

## 5. Kiểm Tra Embedding Quality

Viết script test đơn giản.

**Pipeline:**

```
query → embed
  ↓
cosine similarity
  ↓
top-k chunk
```

**Query test ví dụ:**

- Sữa chua có ăn được cho người tiểu đường?
- Đột biến gen có gây bệnh tiểu đường?
- Cách tính lượng đường trong đồ ăn?

Nếu top chunk trả về đúng nội dung liên quan → embedding hoạt động tốt.

## 6. Important Rules

### Không embed metadata

**Sai:**

```
title + heading + text
```

Vì sẽ làm vector bị nhiễu.

**Đúng:**

```python
embed(text)
# Metadata lưu riêng
```

### Vector Normalization

Nếu dùng cosine similarity:

```
vector / ||vector||
```

Một số thư viện embedding tự normalize, nhưng nên kiểm tra để đảm bảo consistency.

---

# Embedding Module Implementation

## Overview

The Embedding module converts text chunks into vector embeddings for the RAG system.

This implementation follows the specification in `docs/project_spec_embedder.md` and consists of two main files:

- **`embedder.py`**: Reusable embedding wrapper class
- **`embed_chunks.py`**: Pipeline script for batch embedding

## Files Implemented

### 1. `src/embedder/embedder.py`

A production-ready wrapper around HuggingFace sentence transformers.

**Class: `Embedder`**

```python
Embedder(
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    device: str = "cpu",
    normalize: bool = True
)
```

**Key Methods:**

- **`embed(text: str) -> List[float]`**
  - Embeds a single text string
  - Returns normalized 384-dimensional vector
  - Automatically handles tokenization and inference

- **`embed_batch(texts: List[str]) -> List[List[float]]`**
  - Embeds multiple texts efficiently in one batch
  - Uses GPU/CPU batch inference (much faster than one-by-one)
  - Returns list of 384-dimensional vectors

**Features:**

✓ Full type hints and docstrings
✓ Mean pooling with attention mask (ignores padding tokens)
✓ L2 vector normalization for cosine similarity
✓ GPU support with device selection
✓ Model loads once during initialization
✓ Production-ready error handling

**Mean Pooling Implementation:**

```python
sum(token_embeddings * attention_mask) / sum(attention_mask)
```

Ensures padding tokens are correctly ignored during pooling.

### 2. `src/embedder/embed_chunks.py`

Complete embedding pipeline for batch processing chunks.

**Main Function: `embed_chunks()`**

```python
embed_chunks(
    input_path: Path = Path("data/chunked"),
    output_path: Path = Path("data/embedded"),
    batch_size: int = 32,
    device: str = "cpu",
    model_name: str = "...",
    skip_existing: bool = True
)
```

**Pipeline Steps:**

1. Load chunks from `data/chunked/chunked.jsonl`
2. Extract text fields
3. Embed in batches of 32 for performance
4. Attach embeddings to chunks
5. Preserve all metadata (title, heading, position)
6. Save to `data/embedded/embedded_chunks.jsonl`

**Features:**

✓ **Batch Processing**: 32 chunks per batch for GPU/CPU efficiency
✓ **Progress Bar**: Uses tqdm to show real-time progress
✓ **Caching**: Skips chunks that already have embeddings
✓ **Metadata Preservation**: Never modifies metadata
✓ **Error Handling**: Robust file I/O and validation

**Command Line Usage:**

```bash
python -m src.embedder.embed_chunks \
    --input data/chunked \
    --output data/embedded \
    --batch-size 32 \
    --device cpu
```

## Input/Output Schema

### Input: `chunked.jsonl`

Each line is a JSON chunk:

```json
{
  "chunk_id": "chunk_001",
  "doc_id": "doc_001",
  "text": "Lorem ipsum dolor sit amet...",
  "metadata": {
    "title": "Document Title",
    "heading": "Section Heading",
    "position": 1
  }
}
```

### Output: `embedded_chunks.jsonl`

Each line adds an embedding field:

```json
{
  "chunk_id": "chunk_001",
  "doc_id": "doc_001",
  "text": "Lorem ipsum dolor sit amet...",
  "embedding": [0.123, -0.456, 0.789, ... (384 dims total)],
  "metadata": {
    "title": "Document Title",
    "heading": "Section Heading",
    "position": 1
  }
}
```

## Model Details

**Default Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

**Embedding Dimension:** 384

**Features:**
- Multilingual support (including Vietnamese)
- Lightweight and fast
- Good semantic understanding
- Suitable for medium-sized datasets

## Performance Optimization

### Batch Embedding

The implementation uses batch embedding instead of processing chunks one-by-one:

```python
batch_size = 32
```

**Benefits:**
- 50-100x faster than sequential embedding
- Better GPU utilization
- Reduced memory fragmentation

### Caching

Chunks that already have embeddings are skipped:

```python
skip_existing=True  # (default)
```

Prevents redundant recomputation of embeddings.

### Progress Tracking

Real-time progress bar using `tqdm`:

```
Embedding chunks: 45%|████████░░░░░░░░░░| 450/1000 [00:30<00:35, 15 batches/s]
```

## Vector Normalization

All embeddings are **L2 normalized** by default:

```python
vector = vector / ||vector||
```

This ensures:
- Consistent cosine similarity calculations
- Unit-length vectors
- Better performance in vector databases

## Important Rules

### Only Text is Embedded

**WRONG:**
```python
embed(title + heading + text)  # ✗ Metadata is embedded
```

**CORRECT:**
```python
embed(text)  # ✓ Only text, metadata preserved separately
```

Metadata is never concatenated or modified—it's preserved as-is.

## Code Quality

✓ **Type Hints**: Full type annotations throughout
✓ **Docstrings**: Comprehensive docstrings for all functions/classes
✓ **Error Handling**: Robust error handling and validation
✓ **Modularity**: Separates concerns (Embedder vs. Pipeline)
✓ **Readability**: Clear variable names and logical flow
✓ **Production Ready**: Tested patterns, no unnecessary complexity

## Usage Examples

### Example 1: Embed Single Text

```python
from src.embedder import Embedder

embedder = Embedder(device="cpu")
embedding = embedder.embed("What is diabetes?")
print(len(embedding))  # 384
```

### Example 2: Batch Embedding

```python
texts = [
    "Diabetes is a metabolic disease",
    "Blood sugar control is important",
    "Insulin regulates glucose"
]

embeddings = embedder.embed_batch(texts)
print(len(embeddings))      # 3
print(len(embeddings[0]))   # 384
```

### Example 3: Full Pipeline

```python
from pathlib import Path
from src.embedder.embed_chunks import embed_chunks

embed_chunks(
    input_path=Path("data/chunked"),
    output_path=Path("data/embedded"),
    batch_size=32,
    device="cuda",  # Use GPU if available
    skip_existing=True
)
```

## Dependencies

Required packages:

```
torch
transformers
numpy
tqdm
```

Install with:

```bash
pip install torch transformers numpy tqdm
```

## Testing

### Test Single Embedding

```python
embedder = Embedder()
vec = embedder.embed("test")
assert len(vec) == 384, "Embedding should be 384-dimensional"
assert abs(sum(x**2 for x in vec) - 1.0) < 1e-6, "Vector should be normalized"
```

### Test Batch Embedding Quality

Top-k similarity search to verify embeddings make semantic sense:

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

texts = [
    "sữa chua có ăn được cho người tiểu đường?",
    "đột biến gen có gây bệnh tiểu đường?",
    "cách tính lượng đường trong đồ ăn?",
]

embeddings = embedder.embed_batch(texts)
similarities = cosine_similarity(embeddings)
# Similarity matrix should show semantic relationships
```

## Architecture Diagram

```
Raw Documents
    ↓
Chunking Stage (produces chunked.jsonl)
    ↓
Embedding Module (THIS)
  ├─ Embedder: Convert text → vector
  └─ embed_chunks: Batch pipeline
    ↓
Vector Database Ready (embedded_chunks.jsonl)
    ↓
RAG Retrieval Stage
```

## Future Enhancements

- [ ] Support multiple embedding models
- [ ] Async embedding for CPU/GPU overlap
- [ ] Dimension reduction (PCA)
- [ ] Embeddings compressor (quantization)
- [ ] Performance benchmarking tools
- [ ] ONNX export for inference optimization

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [HuggingFace Model Hub](https://huggingface.co/models)
- [Mean Pooling Explained](https://github.com/UKPLab/sentence-transformers)
