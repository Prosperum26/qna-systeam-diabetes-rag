
## Environment
- **Virtualenv**: `venv\Scripts\activate`

# Crawler Requirements

  ## Architecture Overview
  - **BaseCrawler**
    - `fetch()`: tải HTML từ URL (có retry, delay giữa các request).
    - `parse()`: trích xuất dữ liệu sạch (title, nội dung, sections, metadata).
    - `save()`: lưu dữ liệu ra file (raw HTML + JSON đã xử lý).
  - **DiabetesCrawler(BaseCrawler)**
    - Cài đặt cụ thể cho website tiểu đường `yhoccongdong.com`.
    - Cài đặt rule cho category `/tieu-duong/`, selector, normalize, duplicate, safety.
  - **Link discovery**
    - Hàm bắt buộc: `get_article_links()`.
    - Tìm link bài viết trong thẻ `<a href="...">` theo selector và rule phía dưới.

  ---

  ## 1. Scope
  - **Category cần crawl**: toàn bộ bài viết thuộc category:
    - `https://yhoccongdong.com/tieu-duong/`
  - **Pagination**
    - Bao gồm tất cả các trang phân trang nếu có:
      - `https://yhoccongdong.com/tieu-duong/page/2`
      - `https://yhoccongdong.com/tieu-duong/page/3`
      - ...

  ---

  ## 2. Category Page Structure

  ### 2.1 Article Card Structure
  Mỗi bài viết trên category page có cấu trúc:

  ```html
  <div class="post-item_content row px-0">
    <a class="col-12 post-item_content-title" href="[ARTICLE_URL]">
      <h4 class="color-linear">[ARTICLE_TITLE]</h4>
    </a>
  </div>
  ```

  ---

  ## 3. Link Extraction Requirements

  ### 3.1 Selector Strategy
  - **Primary selector**:
    - `a.col-12.post-item_content-title`
  - **Fallback selector**:
    - `div.post-item_content a:has(h4)`

  ### 3.2 Validation Rules
  Đối với mỗi thẻ `<a>` candidate:

  - **Điều kiện bắt buộc**
    - Phải chứa thẻ `<h4>` bên trong.
  - **Điều kiện với `href`**
    - Bắt đầu với: `https://yhoccongdong.com/`
    - Có chứa: `/tieu-duong/`
    - Không được chứa:
      - `/page/`
      - `#`
      - `javascript:`

  ### 3.3 Extracted Fields (Category Page)
  Với mỗi bài trên category page, trích xuất:

  ```json
  {
    "title": "...",
    "url": "...",
    "category": "tieu-duong"
  }
  ```

  ---

  ## 4. URL Normalization Rules
  Trước khi lưu/so sánh duplicate, URL phải được chuẩn hóa:

  - Bỏ dấu `/` ở cuối (trailing slash) để đồng bộ.
  - Loại bỏ toàn bộ query tracking `utm_*`.
  - Loại bỏ fragment (`#...`).
  - Convert về lowercase (trừ khi có path case-sensitive đặc biệt – hiện tại không dùng).

  ---

  ## 5. Duplicate Handling Strategy
  Chiến lược phát hiện trùng:

  1. **URL set check**
    - Kiểm tra URL đã xuất hiện trong tập URL đã crawl (sau khi normalize) hay chưa.
  2. **MD5 hash của nội dung đã chuẩn hóa**
    - Tạo MD5 hash trên nội dung bài viết sau khi:
      - Normalize Unicode (NFC).
      - Normalize whitespace (space/newline).
      - Loại bỏ boilerplate (footer, share, related posts, comment, …).
    - Dùng hash này để phát hiện document trùng nội dung.
  3. **Title comparison (fallback)**
    - Nếu URL + hash không phân biệt được, dùng so sánh title như một fallback cuối.

  Hash **phải được compute SAU** các bước chuẩn hóa nội dung ở trên.

  ---

  ## 6. Article Page Parsing Requirements
  Từ mỗi trang bài viết, cần trích xuất:

  - **Required**
    - `title`: lấy từ `h1` hoặc main heading của bài.
    - `main content`: phần nội dung chính của bài.
  - **Preserve**
    - Thẻ heading và cấu trúc:
      - `h1`
      - `h2`
      - `h3`
    - Văn bản:
      - `p`
      - `ul` / `li` (đặc biệt với phần hướng dẫn/chỉ định y khoa).
  - **Must Remove**
    - `script`, `style`
    - `nav`, `footer`
    - sidebar
    - related posts
    - comment section
    - share buttons
    - Ads/boilerplate khác không thuộc nội dung chính.

  ---

  ## 7. Unicode Handling
  Sau khi fetch và trích xuất text:

  - Set đúng encoding:
    - `response.encoding = response.apparent_encoding`
  - Normalize Unicode:
    - `unicodedata.normalize("NFC", text)`
  - Thay thế ký tự:
    - `\xa0` → space thường.
  - Normalize whitespace:
    - Multiple spaces → single space.
    - Multiple newlines → single newline.

  ---

  ## 8. Raw & Processed Storage

  ### 8.1 Raw HTML
  - Địa chỉ lưu:
    - `data/raw/{slug}.html`
  - `{slug}` lấy từ phần cuối URL bài viết (sau khi normalize).

  ### 8.2 Clean Document JSON
  - Địa chỉ lưu:
    - `data/documents/{slug}.json`
  - Schema:

  ```json
  {
    "doc_id": "...",
    "url": "...",
    "title": "...",
    "category": "tieu-duong",
    "sections": [
      {
        "heading": "Nguyên nhân",
        "content": "..."
      }
    ],
    "metadata": {
      "crawl_time": "...",
      "hash": "md5..."
    }
  }
  ```

  Ghi chú:
  - `doc_id`: có thể là `{slug}` hoặc UUID.
  - `url`: URL bài viết đã normalize.
  - `sections`: danh sách section theo heading (xem mục 9).
  - `metadata.hash`: MD5 hash của nội dung sau chuẩn hóa.

  ---

  ## 9. Section Preservation Strategy
  Yêu cầu giữ nguyên cấu trúc sections, **không flatten** toàn bộ thành một text blob.

  - `h1` → **document title**
  - `h2` → **major section**
  - `h3` → **subsection** bên trong `h2` gần nhất.
  - Paragraphs (`p`, `ul/li`) được gán vào **heading gần nhất phía trên**:
    - Nếu nằm dưới `h2` nhưng trước `h3` → thuộc về section `h2`.
    - Nếu nằm dưới `h3` → thuộc subsection đó.

  Kết quả cuối cùng: document được biểu diễn thành mảng `sections` như trong schema mục 8.

  ---

  ## 10. Crawl Safety
  Crawler phải:

  - Tôn trọng rate limiting:
    - Delay 1–2 giây giữa các request (có thể cấu hình).
  - Xử lý HTTP errors:
    - Retry tối đa 3 lần cho các lỗi tạm thời (5xx, timeout).
    - Nếu vẫn lỗi → đánh dấu URL là failed và bỏ qua.
  - Bỏ qua/bỏ qua mềm:
    - Skip broken links (404, 500, parse error nặng).
  - Logging:
    - Log đầy đủ:
      - URL đã crawl thành công.
      - URL bị lỗi (kèm status code/exception).
      - Thời điểm crawl (`crawl_time`).

  ---

# RAG & Chunking Requirements

## 12. Chunking Strategy

### 12.1 Overall Strategy – Hybrid Section-aware + Sliding Window

Chiến lược chunking sử dụng mô hình HYBRID:

1. **Chunk theo section trước** (giữ cấu trúc heading từ crawler).
2. Nếu section > max token → split bằng sliding window.
3. Nếu section quá nhỏ → merge với section kế tiếp (nếu cùng logic).

Mục tiêu:
- Giữ ngữ nghĩa đầy đủ.
- Không phá vỡ cấu trúc y khoa.
- Tối ưu cho embedding model giới hạn ~512 tokens.

---

### 12.2 Section Normalization

Trước khi chunk:

- Nếu heading rỗng → gán mặc định:
  - `"Giới thiệu"` hoặc `"Mở đầu"`
- Trim whitespace.
- Loại bỏ line break thừa.
- Normalize Unicode (NFC).
- Normalize whitespace:
  - Multiple spaces → single space.
  - Multiple newlines → single newline.

---

### 12.3 Token Counting

Phải dùng tokenizer của embedding model:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

Tất cả rule chunking phải dựa trên **số token thực tế** từ tokenizer này.

### 12.4 Chunking Rules

Vì embedding model có max ~512 tokens nên:

- **Không để chunk > ~450 tokens.**

**Rule cụ thể:**

- **Nếu section ≤ 450 tokens**  
  → 1 section = 1 chunk.

- **Nếu section > 450 tokens** → split theo sliding window:
  - `chunk_size = 400` tokens
  - `overlap = 60` tokens

- **Nếu section < 120 tokens**  
  → Merge với section kế tiếp (nếu cùng ngữ cảnh logic).

### 12.5 Optimized Parameters (Current Setup)

- **chunk_size**: 380–420 tokens  
- **overlap**: 60 tokens  
- **min_chunk**: 150 tokens  
- **preserve section boundary**: luôn tôn trọng ranh giới section nếu có thể.

Không bao giờ cắt giữa:

- Danh sách bước (step-by-step)
- Bullet list quan trọng
- Quy trình điều trị / hướng dẫn y khoa

13. Chunk Metadata Requirements

Mỗi chunk bắt buộc phải lưu metadata đầy đủ:

```json
{
  "chunk_id": "...",
  "doc_id": "...",
  "title": "...",
  "heading": "...",
  "text": "...",
  "position": 3,
  "token_count": 372
}
```

**Giải thích:**

- **position** → giúp reconstruct document theo thứ tự gốc.
- **heading** → giúp LLM hiểu context và vị trí trong tài liệu.
- **title** → tăng semantic match khi retrieve.
- **token_count** → debug & kiểm soát giới hạn model.

### 13.1 Embedding Strategy

Khi embed, **KHÔNG** chỉ embed content thuần.

Phải embed đầy đủ ngữ cảnh:

- **Title + Heading + Content**

Ví dụ format text đưa vào embedding:

```text
[Cách tính lượng đường và tinh bột trong đồ ăn là gì?]
[Tính lượng bột đường là gì?]
Đúng như tên gọi...
```

Cách này giúp tăng **semantic retrieval accuracy** rõ rệt.

## 14. Context Builder for QA

Khi gửi context cho LLM, **không** format dạng đơn giản:

```text
Context:
chunk1
chunk2
```

Thay vào đó, phải format có cấu trúc rõ ràng, ví dụ:

```text
Dưới đây là thông tin từ tài liệu y khoa:

---
Tiêu đề: ...
Mục: ...
Nội dung: ...
---
```

LLM sẽ tôn trọng nội dung hơn và **ít hallucinate** hơn.

## 15. Retrieval Configuration

Vì không sử dụng reranker riêng:

- **top_k retrieve** = 5
- Rerank bằng **cosine similarity**
- Chỉ feed **2–3 chunk tốt nhất** vào LLM  
  → **Không** bao giờ feed toàn bộ 5 chunk.

Nếu feed quá nhiều:

- LLM sẽ trộn nội dung.
- Dễ synthesize sai.

## 16. QA Prompt Constraints

Prompt phải rõ ràng, ví dụ:

```text
Bạn là trợ lý y khoa.

Chỉ sử dụng thông tin từ CONTEXT bên dưới.
Không được thêm kiến thức bên ngoài.
Nếu câu hỏi không có trong CONTEXT, trả lời:
"Tôi không tìm thấy thông tin trong tài liệu."

CONTEXT:
{retrieved_chunks}

Câu hỏi:
{user_question}

Trả lời:
```

**Mục tiêu:**

- Giảm hallucination.
- Ép model trung thành với corpus.

## 17. Source Handling Strategy

Include source ở mức inline nhẹ.

Ví dụ:

> Theo tài liệu về “Tính lượng bột đường”, việc kiểm tra đường huyết sau 2 giờ ăn giúp nhận diện xu hướng thay đổi.

Không cần:

- Link.
- Citation dạng học thuật.

Chỉ cần mention **title/section** để tăng trust & traceability.

## 18. Suggested `src` Structure

Đề xuất cấu trúc thư mục cho phần RAG (future work):

```text
src/
  chunking/
    chunker.py
    token_counter.py
    rules.py

  retrieval/
    retriever.py
    similarity.py

  rag/
    context_builder.py
    prompt.py
```

## 19. Out of Scope (Current Phase)

Chưa triển khai:

- Reranker model riêng.
- Advanced hybrid search (BM25 + vector).
- Cross-encoder re-ranking.
- Production-grade hallucination detection.
