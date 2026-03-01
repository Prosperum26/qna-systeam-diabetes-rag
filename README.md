# RAG Q&A System - Diabetes (Local)

Framework Python RAG local: crawl web → xử lý dữ liệu → RAG với model local.

## Cấu trúc

```
qna-systeam-diabetes-rag/
├── config.py              # Cấu hình tập trung (URL, model, paths...)
├── main.py                # Entry: crawl | index | ask
├── requirements.txt
├── data/
│   ├── raw/               # Dữ liệu crawl thô
│   ├── processed/         # Chunks đã xử lý
│   └── vectorstore/       # ChromaDB persist
└── src/
    ├── crawler/           # Crawl web → documents
    │   └── scraper.py
    ├── processors/        # Chunk documents
    │   └── chunker.py
    ├── embedder/          # Embed text (sentence-transformers)
    │   └── embedding.py
    ├── vectorstore/       # Lưu & search vector
    │   └── store.py
    ├── llm/               # LLM local (Ollama)
    │   └── model.py
    └── rag/               # Pipeline: retrieve + generate
        └── pipeline.py
```

## Flow

1. **crawl** – Crawl URL trong `config.CRAWL_URL` → lưu `data/raw/`
2. **index** – Load raw → chunk → embed → add vào vectorstore
3. **ask** – Nhận câu hỏi → retrieve context → generate answer

## Cài đặt

```bash
pip install -r requirements.txt
```

Cần Ollama chạy local với model (vd: `ollama run llama3.2`).

## Thứ tự implement

1. `config.py` – Điền `CRAWL_URL`
2. `src/crawler/scraper.py` – Logic crawl
3. `src/processors/chunker.py` – Chunk documents
4. `src/embedder/embedding.py` – Load model, embed
5. `src/vectorstore/store.py` – ChromaDB add/search
6. `src/llm/model.py` – Ollama generate
7. `src/rag/pipeline.py` – Ghép retrieve + generate
8. `main.py` – CLI crawl/index/ask
