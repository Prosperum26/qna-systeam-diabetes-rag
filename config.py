"""
Cấu hình tập trung cho RAG pipeline.
Chỉnh sửa các giá trị tại đây thay vì hardcode trong code.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTORSTORE_PATH = DATA_DIR / "vectorstore"

# Crawler
CRAWL_URL = "https://yhoccongdong.com/tieu-duong/"  # URL trang web cần crawl 
CRAWL_DEPTH = 2  # Độ sâu crawl (số cấp link)

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Embedding (local model, e.g. sentence-transformers)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2" #sentence-transformers

# Vector Store
VECTORSTORE_TYPE = "chroma"  # faiss: optional - chưa implement

# LLM (local, e.g. Ollama, llama.cpp)
LLM_MODEL = "llama3"  # Tên model trong Ollama - Llama 3 8B Instruct (chạy 4-bit) [AI đề xuất] - OWEN, Mistral [thầy đề xuất]
LLM_BASE_URL = "http://localhost:11434"  # Ollama default

# RAG
TOP_K_RETRIEVAL = 5  # Số chunk lấy ra khi retrieve
