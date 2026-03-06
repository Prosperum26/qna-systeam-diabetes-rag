# Retriever Module - Tài liệu Chi Tiết

## 1. Retrieve trong RAG là gì?

**Retrieve** = tìm context liên quan nhất với câu hỏi user.

### Pipeline Logic

```
User Question
    ↓
Query Cleaning
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Top-K Relevant Chunks
    ↓
Đưa vào prompt → LLM trả lời
```

### Cấu hình hiện tại

```
TOP_K_RETRIEVAL = 5
```

→ Hệ thống sẽ lấy 5 chunks gần nhất trong vector space.

---

## 2. Phân chia trách nhiệm module (VectorStore vs Retriever)

### ⚠️ Lỗi thiết kế phổ biến
Nhiều người để retrieve nằm trong vectorstore, điều này là sai.

### ✅ Thiết kế đúng

```
rag/
 ├── retriever/
 │     ├── __init__.py
 │     ├── base.py
 │     └── vector_retriever.py
 └── vectorstore/
      ├── base.py
      ├── chroma_store.py
      └── factory.py
```

### VectorStore - chỉ là database

| Nhiệm vụ | Mô tả |
|---------|-------|
| `add_documents()` | Thêm documents vào store |
| `similarity_search()` | Tìm vector gần nhất |
| `delete()` | Xóa documents |
| `persist()` | Lưu trữ dữ liệu |

**Điểm quan trọng**: Vectorstore không hiểu query, nó chỉ hiểu: `vector → search`

### Retriever - logic tìm kiếm intelligent

| Trách nhiệm | Mô tả |
|------------|-------|
| Text → Embedding | Chuyển query sang vector |
| Gọi VectorStore | Tìm kiếm similarity |
| Return chunks | Trả lại kết quả top-k |
| Query Cleaning | Pre-process query |
| Logging | Debug và monitoring |

**Retriever hiểu**:
- Text query từ user
- Embedding model nào cần dùng
- Vectorstore để gọi

---

## 3. Implementación Retriever

### Bước 1: Query Cleaning

**File**: `src/processors/query_cleaner.py`

```python
import re

def clean_query(query: str) -> str:
    """Xử lý query trước khi embed"""
    query = query.lower()
    query = re.sub(r"[^\w\s]", "", query)  # Xóa ký tự đặc biệt
    return query.strip()
```

**Ví dụ**:
```
Input:  "Triệu chứng tiểu đường???"
Output: "triệu chứng tiểu đường"
```

### Bước 2: Retriever Pipeline

**File**: `src/retriever/vector_retriever.py`

```python
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str):
        pass

class VectorRetriever(BaseRetriever):
    def __init__(self, vectorstore, embedder, top_k=5):
        """
        Args:
            vectorstore: VectorStore instance
            embedder: Embedding model instance
            top_k: Số chunks cần lấy (mặc định 5)
        """
        self.vectorstore = vectorstore
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, query: str):
        """
        Retrieve relevant chunks from vectorstore.
        
        Flow:
            User Query → Clean Query → Embed Query → 
            VectorStore Search → Return Top Chunks
        """
        # Step 1: Clean query
        clean_q = self._clean_query(query)
        logger.info(f"Original query: {query}")
        logger.info(f"Cleaned query: {clean_q}")
        
        # Step 2: Embed query
        query_embedding = self.embedder.embed_query(clean_q)
        
        # Step 3: Vector search
        results = self.vectorstore.similarity_search(
            query_embedding,
            k=self.top_k
        )
        
        # Step 4: Log results
        self._log_retrieval_results(results)
        
        return results
    
    @staticmethod
    def _clean_query(query: str) -> str:
        """Pre-process query"""
        import re
        query = query.lower()
        query = re.sub(r"[^\w\s]", "", query)
        return query.strip()
    
    @staticmethod
    def _log_retrieval_results(results):
        """Log retrieved chunks with similarity scores."""
        
        logger.info(f"Retrieved {len(results)} chunks:")

        for idx, result in enumerate(results, 1):

            score = result.get("score")
            text = result.get("text", "")

            if isinstance(score, (int, float)):
                score_str = f"{score:.3f}"
            else:
                score_str = "N/A"

            logger.info(
                f"[{idx}] score={score_str} | {text[:100]}..."
            )
```

### Bước 3: Logging - Debug & Monitoring

Logging nên đặt bên trong retriever để track quá trình:

**Ví dụ output log**:
```
INFO: Original query: Triệu chứng tiểu đường là gì?
INFO: Cleaned query: triệu chứng tiểu đường là gì
INFO: Retrieved 5 chunks:
  [1] score=0.82 | Triệu chứng của bệnh tiểu đường bao gồm...
  [2] score=0.79 | Dấu hiệu nhận biết bệnh tiểu đường...
  [3] score=0.75 | Các biến chứng của tiểu đường...
  [4] score=0.72 | Cách chẩn đoán bệnh tiểu đường...
  [5] score=0.65 | Nguyên nhân gây ra bệnh tiểu đường...
```

**Log này giúp bạn debug**:
- ✓ Chunking có đúng không?
- ✓ Embedding có semantic không?
- ✓ Retrieve có trả về kết quả phù hợp không?

---

## 4. Output của Retriever

Retriever **không** trả lời câu hỏi, nó chỉ trả về:

```python
List[Dict]
```

**Ví dụ**:
```python
[
    {
        "text": "Triệu chứng của bệnh tiểu đường bao gồm...",
        "score": 0.82,
        "source": "docs/tieu-duong.html",
        "chunk_id": "chunk_001"
    },
    {
        "text": "Dấu hiệu nhận biết bệnh tiểu đường...",
        "score": 0.79,
        "source": "docs/tieu-duong.html",
        "chunk_id": "chunk_002"
    },
    # ... thêm 3 chunks khác
]
```

Sau đó **RAG pipeline sẽ build prompt** với các chunks này để LLM trả lời.

---

## 5. Vai trò của Retriever trong toàn bộ RAG Pipeline

```
User Question
     ↓
Query Cleaner (xử lý input)
     ↓
Retriever (tìm context liên quan)
     ↓
Top-K Chunks
     ↓
Prompt Builder (tạo prompt với context)
     ↓
LLM (llama3 qua Ollama)
     ↓
Answer
```

---

## 6. Checklist Implementation

### ✅ Bắt buộc
- [ ] `BaseRetriever` - interface abstract
- [ ] `VectorRetriever` - implementation chính
- [ ] Query cleaning - xử lý query
- [ ] Vector search - tìm kiếm
- [ ] Top-K retrieval - lấy k chunks

### 📌 Nên có
- [ ] Logging query
- [ ] Logging similarity scores
- [ ] Logging retrieved text
- [ ] Error handling
- [ ] Unit tests

---

## 7. Files cần tạo/sửa

```
src/
├── processors/
│   ├── query_cleaner.py (CREATE)
│   └── ... (existing)
└── retriever/
    ├── __init__.py (CREATE)
    ├── base.py (CREATE)
    └── vector_retriever.py (CREATE)
```

---

## 📚 Tham khảo

- **VectorStore**: chỉ là database, làm `similarity_search()`
- **Retriever**: orchestrate query → embedding → search → return chunks
- **Logging**: critical for debugging embedding quality & retrieval accuracy

6️⃣ Output của Retriever nên là gì

Retriever không trả lời câu hỏi.

Nó chỉ trả về:

List[Chunks]

Ví dụ:

[
 {
  "text": "...triệu chứng tiểu đường...",
  "score": 0.82,
  "source": "yhoccongdong.com"
 },
 ...
]

Sau đó RAG pipeline sẽ build prompt.

7️⃣ Vai trò của Retriever trong toàn pipeline

Pipeline RAG hoàn chỉnh của bạn nên là:

User Question
      ↓
Query Cleaner
      ↓
Retriever
      ↓
Top-K chunks
      ↓
Prompt Builder
      ↓
LLM (Ollama llama3)
      ↓
Answer
8️⃣ Module structure đề xuất cho project bạn

Bạn đang có:

src/
 ├── retriever

Bạn nên thiết kế:

retriever/
 ├── base.py
 └── vector_retriever.py
base.py
from abc import ABC, abstractmethod

class BaseRetriever(ABC):

    @abstractmethod
    def retrieve(self, query: str):
        pass
vector_retriever.py
class VectorRetriever(BaseRetriever):

    def __init__(self, vectorstore, embedder, top_k):
        self.vectorstore = vectorstore
        self.embedder = embedder
        self.top_k = top_k

    def retrieve(self, query: str):

        query_embedding = self.embedder.embed_query(query)

        results = self.vectorstore.similarity_search(
            query_embedding,
            k=self.top_k
        )

        return results

10️⃣ Thứ bạn cần implement ngay bây giờ

Checklist cho module retrieve của bạn:

Bắt buộc

✅ BaseRetriever
✅ VectorRetriever
✅ query cleaning
✅ vector search
✅ top-k retrieval

Nên có

✅ logging query
✅ logging similarity score
✅ logging retrieved text