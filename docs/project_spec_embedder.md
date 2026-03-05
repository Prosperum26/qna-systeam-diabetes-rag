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
