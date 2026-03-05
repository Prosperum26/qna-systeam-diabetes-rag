# Architecture

## Folder Structure
- **`crawler/`**
  - `scraper.py`: triển khai `BaseCrawler`, `DiabetesCrawler`, `get_article_links()`, `fetch()`, `parse()`, `save()`.
- **`processors/`**
  - `cleaner.py`: remove `script`, `style`, `nav`, `footer`, ads, comment section, sidebar, related posts, share buttons.
  - `normalizer.py`: chuẩn hóa whitespace, newline, Unicode, thay `\xa0` → space.
  - `section_splitter.py`: tách document theo `h1`, `h2`, `h3`, gom `p`, `ul`, `li` vào section gần nhất.
- **`data/`**
  - `raw/`: lưu raw HTML của từng bài viết, dạng `data/raw/{slug}.html`.
  - `documents/`: lưu document JSON đã clean/structed (1 file / 1 bài), dạng `data/documents/{slug}.json`.

> Ghi chú: Không còn `chunker.py` và thư mục `data/chunks/` trong phase hiện tại. Chunking/RAG được đưa vào phần **Future Work**.

---

## Data Flow

- **1. Link Discovery (Category Pages)**
  - `DiabetesCrawler.get_article_links()`:
    - Crawl từ:
      - `https://yhoccongdong.com/tieu-duong/`
      - Và các trang phân trang `/page/2`, `/page/3`, ...
    - Dùng selector:
      - Primary: `a.col-12.post-item_content-title`
      - Fallback: `div.post-item_content a:has(h4)`
    - Validation cho mỗi `<a>`:
      - Chứa thẻ `<h4>` bên trong.
      - `href`:
        - Bắt đầu với `https://yhoccongdong.com/`
        - Chứa `/tieu-duong/`
        - Không chứa `/page/`, `#`, `javascript:`
    - Trả về danh sách:
      - `{"title": "...", "url": "...", "category": "tieu-duong"}`

- **2. Crawl & Raw Save**
  - `DiabetesCrawler.fetch(url)`:
    - Thêm delay 1–2 giây giữa các request.
    - Set `response.encoding = response.apparent_encoding`.
    - Retry tối đa 3 lần nếu gặp lỗi tạm thời (timeout, 5xx).
  - Lưu raw HTML:
    - Path: `data/raw/{slug}.html`.

- **3. Clean & Normalize**
  - `cleaner`:
    - Remove:
      - `script`, `style`
      - `nav`, `footer`
      - sidebar
      - related posts
      - comment section
      - share buttons
      - boilerplate, ads, block "Contact us", "Share this article", ...
  - `normalizer`:
    - Chuẩn hóa Unicode: `unicodedata.normalize("NFC", text)`.
    - Thay `\xa0` → space thường.
    - Chuẩn hóa whitespace:
      - Multiple spaces → single space.
      - Multiple newlines → single newline.

- **4. Structure Preservation & Sections**
  - `section_splitter`:
    - Xác định:
      - `h1` → document title.
      - `h2` → major section.
      - `h3` → subsection thuộc `h2` gần nhất.
    - Gom các `p`, `ul`, `li` vào heading gần nhất ở phía trên.
    - Kết quả: danh sách `sections` dạng:
      - `{"heading": "...", "content": "..."}`.

- **5. Duplicate Handling**
  - Trước khi lưu document:
    - Normalize URL:
      - Bỏ trailing slash.
      - Bỏ query `utm_*`.
      - Bỏ fragment `#...`.
      - Convert lowercase (nếu không có constraint khác).
    - Kiểm tra:
      1. `URL set check`: URL đã có trong tập đã lưu chưa.
      2. Hash nội dung:
         - Tạo MD5 hash trên text đã:
           - Normalize Unicode (NFC).
           - Normalize whitespace.
           - Loại bỏ boilerplate.
      3. Title comparison:
         - So sánh title giống nhau như một fallback.

- **6. Document Save**
  - Sau khi clean + normalize + tách section:
    - Build object:
      - `doc_id`: `{slug}` hoặc UUID.
      - `url`: URL đã normalize.
      - `title`: từ `h1`.
      - `category`: `"tieu-duong"`.
      - `sections`: danh sách section (xem dưới).
      - `metadata`:
        - `crawl_time`
        - `hash` (MD5 nội dung sau chuẩn hóa).
  - Ghi ra file:
    - `data/documents/{slug}.json`.

- **7. Logging & Error Handling**
  - Log:
    - URL thành công (kèm thời gian).
    - URL lỗi (status code hoặc exception).
  - Bỏ qua mềm (skip) các URL:
    - 404, 500, hoặc parse error không recover được.

---

## Document Schema

- **File location**: `data/documents/{slug}.json`
- **Schema**
  - `doc_id: string`
  - `url: string`
  - `title: string`
  - `category: string` (fixed: `"tieu-duong"`)
  - `sections: Array<{ heading: string, content: string }>`
  - `metadata: { crawl_time: string, hash: string }`

---

## Future Work / Non-Goals (Current Phase)

Các phần dưới **không** thực hiện trong phase hiện tại, nhưng kiến trúc được thiết kế để sẵn sàng hỗ trợ:

- **Chunking & Chunks Storage**
  - Tạo section-level chunks hoặc sliding-window chunks từ `sections`.
  - Lưu vào `data/chunks/chunks.jsonl` với schema:
    - `chunk_id`, `doc_id`, `section`, `text`, `url`, `title`, `category`.
- **Embeddings & Vector Store**
  - Sinh embedding cho từng chunk.
  - Lưu vào vector store (vd: Chroma, FAISS, pgvector, ...).
- **RAG Pipeline**
  - API trả lời câu hỏi dựa trên:
    - Tìm kiếm theo embedding.
    - Kết hợp context + LLM để sinh câu trả lời.
