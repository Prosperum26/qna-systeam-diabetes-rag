# Vector Store / Index

## 📌 Tổng Quan

### Nhiệm Vụ Chính (3 Nhiệm Vụ)

Vector store là thành phần quan trọng của RAG pipeline với 3 nhiệm vụ chính:

1. **Lưu embeddings** - Lưu trữ vector embeddings của các chunks
2. **Index vectors** - Tạo index để search nhanh
3. **Trả về top-k chunks** - Lấy k chunks liên quan nhất cho query

---

## 🏗️ 1. Kiến Trúc Module

### Thiết Kế Abstraction

Thay vì code trực tiếp với DB, nên tạo abstraction layer để dễ dàng switch giữa các vector store (Chroma, FAISS, etc).

**Cấu trúc thư mục:**

```
vectorstore/
├── base.py              # Abstract base class
├── chroma_store.py      # Chroma implementation
├── faiss_store.py       # FAISS implementation
└── factory.py           # Factory pattern
```

### Base Interface

```python
class VectorStore:
    """Abstract interface cho vector store"""
    
    def add_documents(self, ids, embeddings, documents, metadatas):
        """Thêm documents vào vector store"""
        pass

    def similarity_search(self, query_embedding, top_k):
        """Tìm kiếm k documents tương tự nhất"""
        pass

    def persist(self):
        """Lưu vector store ra disk"""
        pass

    def load(self):
        """Load vector store từ disk"""
        pass
```

### Lợi Ích của Abstraction

- ✅ Config chỉ cần đổi `chroma` → `faiss`
- ✅ Code logic không cần sửa
- ✅ Dễ test và switch implementation

---

## 🔧 2. Schema Collection trong Chroma

### Cấu Hình Collection

Khi tạo collection trong Chroma, cần set các thông số:

```python
collection_name = "diabetes_knowledge_base"
embedding_dimension = 384
distance_metric = "cosine"
```

### Embedding Configuration

| Thông Số | Giá Trị |
|----------|--------|
| **Model** | `paraphrase-multilingual-MiniLM-L12-v2` |
| **Dimension** | 384 |
| **Language** | Multilingual (hỗ trợ Tiếng Việt) |

⚠️ **Lưu ý:** Embedding dimension phải khớp với model, nếu không sẽ gây lỗi khi insert.

---

## 🔄 3. Flow Indexing Chuẩn

### Pipeline Indexing

Indexing pipeline nên tách rõ các bước như sau:

```
load chunks
    ↓
embed chunks
    ↓
create vector store
    ↓
add documents
    ↓
persist index
```

### Code Example

```python
# Load chunks từ file
chunks = load_chunks()

# Embed all chunks
embeddings = embedder.embed_batch(
    [c["text"] for c in chunks]
)

# Add vào vector store
vectorstore.add_documents(
    ids=[c["chunk_id"] for c in chunks],
    documents=[c["text"] for c in chunks],
    embeddings=[c["embedding"] for c in chunks],
    metadatas=[c["metadata"] for c in chunks]
)

# Persist to disk
vectorstore.persist()
```

### Cấu Trúc Data Folder

```
data/
├── raw/              # HTML files gốc
├── documents/        # JSON processed documents
├── embedded/         # Embedded chunks
└── vectorstore/      # Vector store index
    ├── chroma.sqlite3
    └── index/
```

---

## 🔍 4. Retriever - Sau Vector Store

### Flow Retriever

Sau khi store xong, retriever sẽ làm các bước:

```
query (text)
    ↓
query embedding
    ↓
vector similarity search
    ↓
top_k chunks
```

### Code Example

```python
# Retrieve top-k chunks
results = vectorstore.similarity_search(
    query_embedding=query_embedding_vector,
    top_k=TOP_K_RETRIEVAL
)

# Results format
[
    {
        "chunk_id": "chunk_123",
        "text": "...",
        "score": 0.85,
        "metadata": {"title": "...", "source": "..."}
    },
    ...
]
```

### ⚠️ Common Bug: Text Mismatch

**Lỗi rất phổ biến:** Index text khác với text embed

```python
# ❌ WRONG - Mismatch!
embed:  cleaned_text
store:  raw_text

# ✅ CORRECT - Consistent!
embed:  cleaned_text
store:  cleaned_text
```

**Kết quả:** → retrieval sẽ mismatch context, LLM sẽ nhận sai context.

### Schema Lưu Vector

```json
{
    "chunk_id": "chunk_001_doc_diabetes_basics",
    "doc_id": "doc_diabetes_basics",
    "text": "Tiểu đường là bệnh về chuyển hóa đường...",
    "embedding": [0.123, 0.456, ...],
    "metadata": {
        "title": "Cơ Bản Về Bệnh Tiểu Đường",
        "heading": "Định Nghĩa",
        "position": 2,
        "source": "diabetes_basics.html"
    }
}
```

---

## ⚙️ 5. Kiểm Tra Dimension Khi Insert

### Bug Phổ Biến

Một bug rất phổ biến khi insert embeddings: không check dimension match.

**Embedding Model:**
- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Dimension: **384**

### Validation Code

```python
def add_embeddings(embeddings):
    """Add embeddings với dimension validation"""
    
    EXPECTED_DIM = 384
    
    for embedding in embeddings:
        if len(embedding) != EXPECTED_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: "
                f"expected {EXPECTED_DIM}, got {len(embedding)}"
            )
    
    # Add to vector store
    vectorstore.add_documents(...)
```

### Tại Sao Quan Trọng?

❌ Nếu không check, sau này khi đổi model (VD: dimension 768) sẽ crash index.

---

## 📦 6. Batch Insert (Rất Quan Trọng Cho Dataset Lớn)

### Vấn Đề Với Large Dataset

Nếu dataset lớn (10000+ chunks), insert một lần có thể:
- ❌ Vượt memory limit
- ❌ Chậm và không stable
- ❌ Khó debug nếu fail giữa chừng

### Solution: Batch Insert

```python
BATCH_SIZE = 64  # hoặc 128 tùy memory

def add_embeddings_batch(chunks, embeddings, metadatas):
    """Add embeddings với batch processing"""
    
    total = len(chunks)
    
    for i in range(0, total, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total)
        batch_chunks = chunks[i:batch_end]
        batch_embeddings = embeddings[i:batch_end]
        batch_metadatas = metadatas[i:batch_end]
        
        vectorstore.add_documents(
            ids=[c["chunk_id"] for c in batch_chunks],
            documents=[c["text"] for c in batch_chunks],
            embeddings=batch_embeddings,
            metadatas=batch_metadatas
        )
        
        print(f"✓ Inserted batch {i}-{batch_end}/{total}")
```

### Lợi Ích

- ✅ Tiết kiệm memory
- ✅ Có thể restart từ batch đó nếu fail
- ✅ Progress tracking tốt hơn

---

## 📊 7. Similarity Score Normalization

### Output Format

Retriever nên trả về kết quả có similarity score:

```python
# Expected format
[
    {
        "chunk_id": "chunk_001",
        "text": "Tiểu đường là...",
        "score": 0.87,
        "metadata": {
            "title": "Định Nghĩa Tiểu Đường",
            "source": "diabetes_101.html"
        }
    },
    {
        "chunk_id": "chunk_002",
        "text": "Các loại tiểu đường...",
        "score": 0.82,
        "metadata": {...}
    }
]
```

### Ích Lợi Của Score

1. **Threshold filtering** - Filter out low-relevance chunks
2. **Debug retrieval** - Xem relevance của từng chunk
3. **Confidence indication** - Biết độ tin cây của retrieval
4. **Ranking** - Rank results theo relevance

---

## 🎯 8. Score Threshold (Rất Hữu Ích)

### Config Threshold

Thêm config để filter chunks không liên quan:

```python
# Config
SIMILARITY_THRESHOLD = 0.5  # Chỉ lấy chunks với score > 0.5
TOP_K_RETRIEVAL = 5
```

### Filtering Logic

```python
def retrieve_with_threshold(query_embedding):
    """Retrieve với score threshold filtering"""
    
    # Get top-k (unfiltered)
    results = vectorstore.similarity_search(
        query_embedding,
        top_k=TOP_K_RETRIEVAL * 2  # Get more để filter
    )
    
    # Filter by threshold
    filtered = [
        r for r in results 
        if r["score"] >= SIMILARITY_THRESHOLD
    ]
    
    # Return top-k filtered results
    return filtered[:TOP_K_RETRIEVAL]
```

### Lợi Ích

- ✅ Tránh LLM nhận context không liên quan
- ✅ Giảm noise trong RAG pipeline
- ✅ Cải thiện quality của LLM answer

---

## 🔗 9. Deduplicate Chunks

### Vấn Đề Duplicates

Nếu crawler lấy nhiều pages giống nhau, vector search có thể trả về nhiều chunks từ cùng một article:

```
chunk_1 (from article A, paragraph 1)
chunk_2 (from article A, paragraph 2)
chunk_3 (from article A, paragraph 3)
chunk_4 (from article B, paragraph 1)  ← Different article
```

### Deduplication Strategy

```python
def deduplicate_results(results, max_per_doc=2):
    """Deduplicate results by doc_id"""
    
    doc_chunks = {}
    deduped_results = []
    
    for result in results:
        doc_id = result["metadata"]["doc_id"]
        
        if doc_id not in doc_chunks:
            doc_chunks[doc_id] = 0
        
        # Only keep max_per_doc chunks per document
        if doc_chunks[doc_id] < max_per_doc:
            deduped_results.append(result)
            doc_chunks[doc_id] += 1
    
    return deduped_results
```

### Lợi Ích

- ✅ Cải thiện diversity của retrieved chunks
- ✅ Tránh redundant information trong LLM context
- ✅ Tốt hơn cho quality answer

---

## 📝 10. Logging Khi Indexing

### Tại Sao Log Quan Trọng?

RAG pipeline rất khó debug nếu không log. Indexing nên log từng bước:

```
loading chunks...
embedding chunks...
creating vector store...
adding documents...
persisting index...
```

### Implementation Example

```python
import logging

logger = logging.getLogger(__name__)

def index_pipeline(chunks_file):
    """Main indexing pipeline với logging"""
    
    # Load chunks
    logger.info("Loading chunks from disk...")
    chunks = load_chunks(chunks_file)
    logger.info(f"✓ Loaded {len(chunks)} chunks")
    
    # Embed chunks
    logger.info("Embedding chunks...")
    start_time = time.time()
    embeddings = embedder.embed_batch(
        [c["text"] for c in chunks]
    )
    embed_time = time.time() - start_time
    logger.info(f"✓ Embedded in {embed_time:.2f}s")
    
    # Create vector store
    logger.info("Creating vector store...")
    vectorstore = create_vectorstore()
    
    # Add documents with batch processing
    logger.info("Adding documents to vector store...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, len(chunks))
        # Add batch...
        logger.info(f"  → Batch {i}-{batch_end}/{len(chunks)}")
    
    # Persist
    logger.info("Persisting vector store...")
    vectorstore.persist()
    logger.info(f"✓ Index saved to {VECTORSTORE_PATH}")
    
    logger.info("✓ Indexing pipeline completed successfully!")
```

### Log Output Example

```
Loading chunks from disk...
✓ Loaded 325 chunks
Embedding chunks...
✓ Embedded in 3.2s
Creating vector store...
Adding documents to vector store...
  → Batch 0-64/325
  → Batch 64-128/325
  → Batch 128-192/325
  → Batch 192-256/325
  → Batch 256-320/325
  → Batch 320-325/325
Persisting vector store...
✓ Index saved to data/vectorstore/
✓ Indexing pipeline completed successfully!
```

---

## ✅ 11. Kiểm Tra Index Tồn Tại

### Problem: Mỗi Lần Run Lại Index Toàn Bộ

Nếu không check, mỗi lần run code lại sẽ re-index toàn bộ dataset → **lãng phí tài nguyên**.

### Solution: Load Existing Index

```python
import os

def get_or_create_vectorstore():
    """Load existing index hoặc create new"""
    
    VECTORSTORE_PATH = "data/vectorstore"
    
    # Check if index exists
    if os.path.exists(VECTORSTORE_PATH) and \
       os.path.exists(os.path.join(VECTORSTORE_PATH, "chroma.sqlite3")):
        
        logger.info(f"Loading existing vector store from {VECTORSTORE_PATH}...")
        vectorstore = ChromaVectorStore.load(VECTORSTORE_PATH)
        logger.info("✓ Vector store loaded")
        return vectorstore
    
    else:
        logger.info("No existing vector store found, creating new one...")
        vectorstore = ChromaVectorStore.create(VECTORSTORE_PATH)
        
        # Run indexing pipeline
        chunks = load_chunks()
        embeddings = embedder.embed_batch([c["text"] for c in chunks])
        
        vectorstore.add_documents(
            ids=[c["chunk_id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            embeddings=embeddings,
            metadatas=[c["metadata"] for c in chunks]
        )
        
        vectorstore.persist()
        logger.info("✓ Vector store created and indexed")
        return vectorstore
```

### Lợi Ích

- ✅ Tiết kiệm thời gian (skip re-indexing)
- ✅ Tiết kiệm tài nguyên (CPU, memory)
- ✅ Nhanh chóng khi develop/iterate

---

## 📋 Summary Table

| Thành Phần | Mục Đích | Lưu Ý |
|-----------|---------|-------|
| **Abstraction** | Dễ switch vector store | Sử dụng base interface |
| **Collection Schema** | Config Chroma | Dimension: 384 |
| **Indexing Pipeline** | Index documents | Batch insert cho dataset lớn |
| **Retriever** | Lấy top-k chunks | Check text consistency |
| **Dimension Validation** | Prevent bugs | Validate trước insert |
| **Batch Insert** | Large dataset handling | 64-128 chunks/batch |
| **Score Normalization** | Quality control | Return score với results |
| **Threshold Filtering** | Remove low-relevance | Config SIMILARITY_THRESHOLD |
| **Deduplication** | Diversity | Max 2 chunks/document |
| **Logging** | Debugging | Log mỗi bước pipeline |
| **Index Caching** | Performance | Load existing, skip re-index |