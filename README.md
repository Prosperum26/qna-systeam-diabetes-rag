# RAG Q&A System - Diabetes (Local)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Status](https://img.shields.io/badge/status-in--development-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![AI](https://img.shields.io/badge/AI-RAG%20System-purple)
![Local LLM](https://img.shields.io/badge/LLM-Local-red)

Một hệ thống RAG (Retrieval-Augmented Generation) hoàn chỉnh cho việc hỏi đáp kiến thức về tiểu đường, được xây dựng với Python và chạy hoàn toàn local.

> ⚠️ **Note:** This project is built mainly for learning and experimentation.  
> The system is still under active development and may change significantly over time.

## 🎯 Mục tiêu

Xây dựng một hệ thống Q&A thông minh có thể:

- Crawl dữ liệu từ các nguồn web về tiểu đường
- Xử lý và chia nhỏ văn bản thành các đoạn có ý nghĩa
- Lưu trữ vector embeddings cho việc tìm kiếm tương đồng
- Trả lời câu hỏi người dùng dựa trên kiến thức đã crawl

## 🏗️ Kiến trúc hệ thống

```
qna-systeam-diabetes-rag/
├── config.py              # Cấu hình tập trung (URL, model, paths...)
├── main.py                # Entry point: crawl | index | ask
├── requirements.txt       # Dependencies
├── data/                  # Data storage
│   ├── raw/              # Dữ liệu crawl thô
│   ├── documents/        # Dữ liệu khi processed.
│   ├── chunked/          # Chunks đã xử lý
│   └── vectorstore/      # ChromaDB persist
├── docs/                 # Documentation
├── tests/                # Unit tests
└── src/                  # Source code
    ├── chunking/         # Text chunking strategies
    ├── crawler/          # Web crawling implementation
    ├── embedder/         # Text embedding generation
    ├── llm/              # Local LLM integration
    ├── pipelines/        # End-to-end pipelines
    ├── processors/       # Text processing utilities
    ├── rag/              # RAG pipeline core
    ├── retriever/        # Vector retrieval logic
    └── vectorstore/      # Vector database operations
```

## 🔄 Workflow

1. **Crawl Phase** – Thu thập dữ liệu từ các nguồn web đã cấu hình
2. **Processing Phase** – Làm sạch, chuẩn hóa và chia nhỏ văn bản
3. **Indexing Phase** – Tạo embeddings và lưu vào vector database
4. **Query Phase** – Nhận câu hỏi, retrieve context, generate answer

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Ollama (cho local LLM)
- Git

### Installation

```bash
# Clone repository
git clone <repository-url>
cd qna-systeam-diabetes-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup Ollama
ollama pull llama3.2  # hoặc model khác
```

### Configuration

Chỉnh sửa `config.py` với các thông số:

- `CRAWL_URL`: URLs để crawl dữ liệu
- `LLM_MODEL`: Tên model Ollama
- `VECTORSTORE_PATH`: Đường dẫn lưu vector database
- `CHUNK_SIZE`: Kích thước chunk
- `CHUNK_OVERLAP`: overlap giữa các chunk / Chưa implement

### Usage

```bash
# Crawl dữ liệu
python src/pipelines/crawl_runner.py - Hiện chưa implement xong, dùng test/crawl_test.py để test crawl dữ liệu

# Index dữ liệu vào vector store
python src/pipelines/build_knowledge.py

# Hỏi đáp
python src/pipelines/chat_pipeline.py
```

## 📚 Module Documentation

Mỗi module trong `src/` có README riêng với chi tiết:

- **[chunking/](src/chunking/README.md)** - Chiến lược chia nhỏ văn bản
- **[crawler/](src/crawler/README.md)** - Crawl và extract web content
- **[embedder/](src/embedder/README.md)** - Tạo text embeddings
- **[llm/](src/llm/README.md)** - Local LLM integration
- **[pipelines/](src/pipelines/README.md)** - End-to-end processing pipelines
- **[processors/](src/processors/README.md)** - Text processing utilities
- **[retriever/](src/retriever/README.md)** - Vector retrieval logic
- **[vectorstore/](src/vectorstore/README.md)** - Vector database operations

## 🛠️ Development

### Adding New Data Sources

1. Thêm URL vào `config.py`
2. Tùy chỉnh crawler trong `src/crawler/`
3. Chạy `python main.py crawl`

### Extending Chunking Strategies

1. Implement new chunker trong `src/chunking/`
2. Register trong `src/chunking/rules.py`
3. Configure trong `config.py`

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_chunking.py
```

## 📊 Performance

- **Crawling**: Tùy thuộc vào số lượng URL và kích thước trang
- **Embedding**: ~1-2s per chunk (sentence-transformers)
- **Retrieval**: <100ms cho 10k chunks (Vẫn chưa optimize và kiểm thử)
- **Generation**: 2-5s per response (Ollama local)

## 🔧 Troubleshooting

### Common Issues

1. **Ollama connection failed**: Đảm bảo Ollama đang chạy
2. **Memory errors**: Giảm chunk size hoặc batch size
3. **Poor retrieval quality**: Tinh chỉnh chunking strategy và embedding model

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Make changes với tests
4. Submit pull request

## 📄 License

[License information]

## 🙏 Acknowledgments

- Sentence Transformers cho embeddings
- Ollama cho local LLM
- ChromaDB cho vector database
- BeautifulSoup cho web scraping
