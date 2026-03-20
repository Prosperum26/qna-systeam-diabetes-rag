# Pipelines Module

Module này cung cấp các pipeline hoàn chỉnh cho hệ thống RAG, bao gồm cả data crawling và chatbot functionality.

## Mục tiêu

- **Data Crawling**: Tự động thu thập và xử lý dữ liệu từ nhiều nguồn
- **RAG Pipeline**: Kết hợp vector retrieval với LLM generation
- **Multi-Source Support**: Hỗ trợ nhiều loại website và cấu hình
- **Scalability**: Thiết kế để xử lý lượng lớn dữ liệu
- **Monitoring**: Comprehensive logging và performance tracking

## Kiến trúc

```
src/pipelines/
├── crawl_runner.py    # Data crawling pipeline
├── chat_pipeline.py   # RAG chat pipeline
├── build_knowledge.py # Knowledge building pipeline
└── README.md          # This file
```

---

## Data Crawling Pipeline (`crawl_runner.py`)

### Overview
`crawl_runner.py` là orchestrator chính cho việc thu thập dữ liệu web, hỗ trợ 2 mode:
- **Config Mode**: Crawl nhiều URLs từ file config
- **Single URL Mode**: Crawl 1 URL cụ thể

### Architecture Flow

```
Config Loading → Site Detection → Crawler Selection → Link Discovery → Article Processing → Data Storage
```

### Key Features

#### **1. Multi-Site Support**
```python
# Automatic site detection
site_type = detect_site_type(url, sites_config)

# Dynamic crawler selection
if site_type in sites_config.get('sites', {}):
    crawler = GenericCrawler(site_config=site_config, ...)
else:
    crawler = DiabetesCrawler(delay_seconds=2.0)
```

#### **2. Sequential Processing**
```python
# Process URLs one by one (as requested)
for url_index, url_config in enumerate(urls, 1):
    # Phase 1: Collect all links from this URL
    article_links = crawler.get_article_links(max_pages=5, max_links=max_article)
    
    # Phase 2: Process all articles from this URL
    for article_link in unique_links:
        _process_single_article(article_link.url, ...)
    
    # Only after ALL articles done → move to next URL
```

#### **3. Dual Storage Strategy**
```
data/
├── raw/           # Original HTML files
│   ├── yhoccongdong_com_article1.html
│   └── who_int_fact_sheet.html
└── documents/     # Processed JSON documents
    ├── yhoccongdong_com_article1.json
    └── who_int_fact_sheet.json
```

### Usage Examples

#### **Config Mode (Default)**
```bash
# Run with default config
python -m src.pipelines.crawl_runner

# Custom config file
python -m src.pipelines.crawl_runner --config custom_config.json

# Show configuration
python -m src.pipelines.crawl_runner --show-config
```

#### **Single URL Mode**
```bash
# Basic single URL
python -m src.pipelines.crawl_runner --url https://example.com

# With custom parameters
python -m src.pipelines.crawl_runner \
  --url https://yhoccongdong.com/tieu-duong/ \
  --category diabetes \
  --depth 2 \
  --max-article 50

# Custom output directory
python -m src.pipelines.crawl_runner \
  --url https://example.com \
  --output-dir custom/data
```

#### **Configuration Structure**
```json
{
  "urls": [
    {
      "url": "https://yhoccongdong.com/tieu-duong/",
      "category": "diabetes",
      "depth": 2,
      "max_article": 50,
      "enabled": true
    },
    {
      "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
      "category": "medical",
      "depth": 1,
      "max_article": 1,
      "enabled": true
    }
  ],
  "global_settings": {
    "default_category": "general",
    "default_depth": 1,
    "default_max_article": 5,
    "default_delay": 2.0
  }
}
```

### Processing Steps

#### **Single Article Processing**
```python
def _process_single_article(url, crawler, output_path, category, depth, max_article):
    # Step 1: Fetch HTML
    html_content = crawler.fetch(url)
    
    # Step 2: Save Raw HTML
    raw_file_path = "data/raw/article.html"
    with open(raw_file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Step 3: Process Content
    soup = BeautifulSoup(html_content, "html.parser")
    clean_article_soup(soup)
    sections = split_sections(soup.body)
    
    # Step 4: Build Document
    document = {
        "doc_id": create_slug_from_url(url),
        "url": crawler.normalize_url(url),
        "title": extract_title(soup),
        "category": category,
        "sections": sections,
        "metadata": {
            "crawl_time": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
            "raw_html_file": raw_file_path
        }
    }
    
    # Step 5: Save Processed Document
    output_file = "data/documents/article.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
```

### Crawler Types

#### **GenericCrawler (Config-Driven)**
- **Multi-site support**: Đọc config từ `sites_config.json`
- **AJAX pagination**: Hỗ trợ "Load More" buttons
- **Traditional pagination**: Hỗ trợ `/page/2/` style
- **Flexible selectors**: CSS selectors tùy chỉnh per site

#### **DiabetesCrawler (Legacy)**
- **Hardcoded logic**: Chuyên cho yhoccongdong.com
- **AJAX optimized**: Implementation chuẩn xác cho WordPress AJAX
- **Fallback option**: Khi GenericCrawler không hoạt động

### AJAX Pagination Features

#### **Config-Driven AJAX**
```json
{
  "pagination": {
    "type": "ajax",
    "ajax": {
      "ajax_url": "https://site.com/wp-admin/admin-ajax.php",
      "action": "watch_more_ar",
      "view": "cancer-default",
      "nonce_param": "_ajax_nonce",
      "headers": {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
      },
      "nonce_patterns": [
        "_ajax_nonce\"\\s*:\\s*\"([a-f0-9]+)\""
      ]
    }
  }
}
```

#### **Robust Implementation**
- **Multiple nonce patterns**: Tìm nonce theo nhiều cách
- **Brotli compression**: Xử lý response nén
- **POST + GET fallback**: Nếu POST fail thì thử GET
- **Header management**: Khôi phục headers sau request

### Performance Features

#### **Rate Limiting**
```python
# Between URLs: Respect rate limits
time.sleep(delay)  # 2s default

# Between articles: Continuous processing
time.sleep(0.5)  # Shorter delay
```

#### **Deduplication**
```python
# O(1) duplicate detection
seen_urls = set()
for link in article_links:
    if link.url not in seen_urls:
        unique_links.append(link)
        seen_urls.add(link.url)
```

---

## 🧠 Knowledge Building Pipeline (`build_knowledge.py`)

### Overview
`build_knowledge.py` là pipeline xử lý documents đã crawled để xây dựng knowledge base cho RAG system:
- **Load Documents**: Đọc JSON files từ `data/documents/`
- **Chunk Documents**: Chia nhỏ documents thành chunks
- **Generate Embeddings**: Tạo vector embeddings cho chunks
- **Store Vectors**: Lưu vào vector database (ChromaDB)

### Architecture Flow

### Architecture Flow

```
Document Loading → Chunking → Embedding Generation → Vector Storage
```

### Key Features

#### **1. Hybrid Chunking Strategy**
```python
chunker = HybridChunker(
    token_counter=token_counter,
    max_tokens_per_chunk=450,
    chunk_size=400,
    overlap=60,
    min_section_tokens=120
)
```

#### **2. Batch Processing**
- **Embedding batches**: 32 chunks per batch
- **Vector storage batches**: 128 vectors per batch
- **GPU/CPU auto-detection**: Tự động chọn device

#### **3. Robust Error Handling**
- **Document-level error recovery**: Skip corrupted files
- **Batch-level fallback**: Zero embeddings cho failed batches
- **Validation**: Kiểm tra data consistency

### Usage Examples

#### **Basic Usage**
```bash
# Run with default settings
python -m src.pipelines.build_knowledge

# Custom data directory
python -m src.pipelines.build_knowledge --data-dir custom/documents

# Custom vector store path
python -m src.pipelines.build_knowledge --store-path custom/vectorstore

# Custom batch size
python -m src.pipelines.build_knowledge --batch-size 64
```

#### **Advanced Usage**
```bash
# High-performance settings
python -m src.pipelines.build_knowledge \
  --data-dir data/documents \
  --store-path data/vectorstore \
  --batch-size 64 \
  --log-level DEBUG

# Memory-efficient settings
python -m src.pipelines.build_knowledge \
  --batch-size 16 \
  --log-level INFO
```

### Processing Steps

#### **Step 1: Document Loading**
```python
def load_documents(data_dir: str = "data/documents") -> List[Dict]:
    # Load all JSON files
    json_files = list(Path(data_dir).glob("*.json"))
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
            documents.append(doc)
    
    return documents
```

#### **Step 2: Document Chunking**
```python
def chunk_documents(documents: List[Dict]) -> List[Dict]:
    chunker = HybridChunker(
        max_tokens_per_chunk=450,
        chunk_size=400,
        overlap=60
    )
    
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
    
    return all_chunks
```

#### **Step 3: Embedding Generation**
```python
def generate_embeddings(chunks: List[Dict], batch_size: int = 32) -> List[List[float]]:
    # Auto device detection
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    embedder = Embedder(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device=device
    )
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_embeddings = embedder.embed_batch(batch_texts)
        embeddings.extend(batch_embeddings)
    
    return embeddings
```

#### **Step 4: Vector Storage**
```python
def store_vectors(chunks, embeddings, store_path):
    # Create ChromaDB vector store
    vectorstore = create_vectorstore(
        path=Path(store_path),
        store_type="chroma"
    )
    
    # Prepare metadata
    metadatas = []
    for chunk in chunks:
        metadata = {
            "doc_id": chunk.get("doc_id", ""),
            "title": chunk.get("title", ""),
            "heading": chunk.get("heading", ""),
            "position": chunk.get("position", 0),
            "url": chunk.get("url", ""),
            "category": chunk.get("category", "")
        }
        metadatas.append(metadata)
    
    # Store in batches
    vectorstore.add_documents(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    # Persist to disk
    vectorstore.persist()
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `data_dir` | "data/documents" | Directory containing JSON documents |
| `store_path` | "data/vectorstore" | Vector store persistence path |
| `batch_size` | 32 | Embedding generation batch size |
| `max_tokens_per_chunk` | 450 | Maximum tokens per chunk |
| `chunk_size` | 400 | Target chunk size |
| `overlap` | 60 | Overlap between chunks |
| `embedding_model` | paraphrase-multilingual-MiniLM-L12-v2 | Sentence transformer model |

### Performance Optimization

#### **Memory Management**
```python
# Process in smaller batches for memory efficiency
batch_size = 16  # Instead of 32

# Clear GPU memory between batches
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

#### **GPU Acceleration**
```python
# Automatic GPU detection
device = "cuda" if torch.cuda.is_available() else "cpu"

# Batch size optimization for GPU
if torch.cuda.is_available():
    batch_size = 64  # Larger batches for GPU
else:
    batch_size = 16  # Smaller batches for CPU
```

### Output Structure

#### **Vector Store Format**
```
data/vectorstore/
├── chroma.sqlite3          # ChromaDB database
├── index/                  # Vector indices
│   ├── id_to_uuid.pkl
│   └── index_header.pkl
└── metadata/               # Document metadata
    ├── chunk_0.json
    ├── chunk_1.json
    └── ...
```

#### **Chunk Metadata Structure**
```json
{
  "chunk_id": "doc1_chunk_0",
  "text": "Chunk content here...",
  "doc_id": "doc1",
  "title": "Document Title",
  "heading": "Section Heading",
  "position": 0,
  "url": "https://example.com/article",
  "category": "diabetes",
  "token_count": 387
}
```

### Monitoring & Debugging

#### **Progress Tracking**
```bash
# Enable detailed logging
python -m src.pipelines.build_knowledge --log-level DEBUG

# Expected output:
# 2026-03-20 08:30:00 [INFO] build_knowledge - Found 150 JSON files in data/documents
# 2026-03-20 08:30:01 [INFO] build_knowledge - Starting document chunking...
# 2026-03-20 08:30:05 [INFO] build_knowledge - Document 1/150: 8 chunks
# 2026-03-20 08:30:05 [INFO] build_knowledge - Generated 1200 total chunks from 150 documents
# 2026-03-20 08:30:06 [INFO] build_knowledge - Starting embedding generation...
# 2026-03-20 08:30:06 [INFO] build_knowledge - Using device: cuda
# 2026-03-20 08:30:10 [INFO] build_knowledge - Batch 1/38: 32 embeddings generated
# 2026-03-20 08:31:45 [INFO] build_knowledge - Generated 1200 embeddings
# 2026-03-20 08:31:46 [INFO] build_knowledge - Starting vector storage...
# 2026-03-20 08:32:00 [INFO] build_knowledge - Vector store successfully persisted to data/vectorstore
```

#### **Performance Metrics**
```python
# Expected performance characteristics:
Documents: 150 files (~50MB)
Chunks: 1,200 chunks (~200MB)
Embeddings: 1,200 vectors (~400MB)
Processing time: ~2-5 minutes (GPU), ~10-15 minutes (CPU)
Memory usage: ~2-4GB peak
```

---

## 🤖 RAG Chat Pipeline (`chat_pipeline.py`)

### Overview
`chat_pipeline.py` cung cấp complete RAG system với vector retrieval và LLM generation.

### Core Components

#### **RAGChatPipeline Class**
```python
class RAGChatPipeline:
    def __init__(
        self,
        vectorstore_path: str = "data/vectorstore",
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        llm_model: str = "llama3",
        ollama_base_url: str = "http://localhost:11434",
        top_k: int = 5,
        max_context_tokens: int = 1500,
        temperature: float = 0.2
    )
```

#### **Pipeline Flow**
```
User Query → Vector Embedding → Similarity Search → Context Building → LLM Generation → Response Formatting
```

### Usage Examples

#### **Programmatic API**
```python
from src.pipelines.chat_pipeline import RAGChatPipeline

# Initialize pipeline
pipeline = RAGChatPipeline(
    vectorstore_path="data/vectorstore",
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    llm_model="llama3",
    top_k=5,
    max_context_tokens=1500
)

# Simple query
response = pipeline.query("What are the symptoms of diabetes?")
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")

# Batch queries
queries = [
    "What is type 1 diabetes?",
    "How is diabetes diagnosed?",
    "What are treatment options?"
]
responses = pipeline.batch_query(queries)
for query, resp in zip(queries, responses):
    print(f"Q: {query}")
    print(f"A: {resp.answer}")
    print("---")
```

#### **CLI Interface**
```bash
# Interactive chat mode
python -m src.pipelines.chat_pipeline chat

# Single query
python -m src.pipelines.chat_pipeline query "What is diabetes?"

# Batch queries from file
python -m src.pipelines.chat_pipeline batch --file queries.txt

# Health check
python -m src.pipelines.chat_pipeline health
```

#### **Advanced Usage**
```python
# Custom pipeline configuration
pipeline = RAGChatPipeline(
    vectorstore_path="custom_vectorstore",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    llm_model="llama3:instruct",
    top_k=10,
    max_context_tokens=2000,
    temperature=0.1
)

# Query with custom options
response = pipeline.query(
    query="Explain diabetes complications",
    include_metadata=True,
    min_relevance_score=0.7
)

# Get detailed statistics
stats = pipeline.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Average response time: {stats['avg_response_time']:.2f}s")
```

#### **CLI Interface**
```bash
# Interactive chat mode
python -m src.pipelines.chat_pipeline chat

# Single query
python -m src.pipelines.chat_pipeline query "What is diabetes?"

# Batch queries from file
python -m src.pipelines.chat_pipeline batch --file queries.txt

# Health check
python -m src.pipelines.chat_pipeline health
```

#### **Advanced Usage**

```python
# Custom pipeline with specific configuration
pipeline = RAGChatPipeline(
    vectorstore_path="custom_vectorstore",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    llm_model="llama3:instruct",
    top_k=10,
    max_context_tokens=2000,
    temperature=0.1
)

# Query with custom options
response = pipeline.query(
    query="Explain diabetes complications",
    include_metadata=True,
    min_relevance_score=0.7
)

# Get detailed statistics
stats = pipeline.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Average response time: {stats['avg_response_time']:.2f}s")
```

## 📊 Configuration

### Pipeline Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `vectorstore_path` | "data/vectorstore" | Path to ChromaDB |
| `embedding_model` | paraphrase-multilingual-MiniLM-L12-v2 | Embedding model |
| `llm_model` | "llama3" | Ollama model name |
| `ollama_base_url` | "http://localhost:11434" | Ollama server |
| `top_k` | 5 | Number of chunks to retrieve |
| `max_context_tokens` | 1500 | Maximum context for LLM |
| `temperature` | 0.2 | LLM sampling temperature |

### Performance Tuning

```python
# For faster responses
fast_pipeline = RAGChatPipeline(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Faster model
    top_k=3,  # Fewer chunks
    max_context_tokens=800  # Smaller context
)

# For higher quality
quality_pipeline = RAGChatPipeline(
    top_k=10,  # More chunks
    max_context_tokens=2000,  # Larger context
    temperature=0.1  # More deterministic
)
```

## 🔍 Response Format

### RAGResponse Structure

```python
@dataclass
class RAGResponse:
    answer: str              # Generated answer
    sources: List[str]       # Source document titles
    chunk_count: int         # Number of chunks used
    context_tokens: int      # Estimated token count
    query_time: float        # Time taken for query
    retrieval_time: float    # Time for retrieval
    generation_time: float   # Time for generation
    chunks_used: List[Dict]  # Actual chunks used (optional)
```

### Example Response

```python
response = pipeline.query("What is diabetes?")

print(f"Answer: {response.answer}")
# Answer: Diabetes is a chronic disease that affects how your body processes glucose...

print(f"Sources: {response.sources}")
# Sources: ['Diabetes Overview', 'Understanding Type 2 Diabetes']

print(f"Used {response.chunk_count} chunks in {response.query_time:.2f}s")
# Used 3 chunks in 1.23s
```

## 📈 Performance Metrics

### Typical Performance

| Operation | Average Time | Notes |
|-----------|--------------|-------|
| Query embedding | ~50ms | CPU, ~10ms GPU |
| Vector search | ~100ms | 10k chunks |
| Context building | ~20ms | 5 chunks |
| LLM generation | ~2-5s | Depends on model |
| **Total** | **~2.5-6s** | End-to-end |

### Monitoring

```python
# Enable performance monitoring
pipeline.enable_monitoring()

# Query multiple times
for _ in range(10):
    pipeline.query("What is diabetes?")

# Get performance stats
stats = pipeline.get_performance_stats()
print(f"Average query time: {stats['avg_query_time']:.2f}s")
print(f"P95 query time: {stats['p95_query_time']:.2f}s")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
```

## 🧪 Testing

```bash
# Run pipeline tests
python -m pytest tests/test_chat_pipeline.py

# Test with sample data
python -c "
from src.pipelines.chat_pipeline import RAGChatPipeline
pipeline = RAGChatPipeline()
response = pipeline.query('What is diabetes?')
print(response.answer)
"

# Performance benchmark
python -m src.pipelines.chat_pipeline benchmark --queries 100
```

### Unit Test Examples

```python
def test_pipeline_initialization():
    pipeline = RAGChatPipeline()
    assert pipeline.vectorstore is not None
    assert pipeline.retriever is not None
    assert pipeline.generator is not None

def test_simple_query():
    pipeline = RAGChatPipeline()
    response = pipeline.query("What is diabetes?")
    assert response.answer is not None
    assert len(response.sources) > 0
```

## 🔧 Customization

### Custom Retrieval Strategy

```python
class CustomPipeline(RAGChatPipeline):
    def retrieve_chunks(self, query: str) -> List[Dict]:
        # Custom retrieval logic
        chunks = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
            filters={"category": "diabetes"}
        )
        
        # Custom relevance scoring
        scored_chunks = []
        for chunk in chunks:
            score = self.calculate_relevance_score(query, chunk)
            if score > 0.7:
                scored_chunks.append(chunk)
        
        return scored_chunks
    
    def calculate_relevance_score(self, query: str, chunk: Dict) -> float:
        # Custom scoring logic
        # Consider semantic similarity, recency, source authority
        return 0.8
```

### Custom Response Processing

```python
class EnhancedPipeline(RAGChatPipeline):
    def process_response(self, response: RAGResponse) -> RAGResponse:
        # Add confidence scores
        response.confidence = self.calculate_confidence(response)
        
        # Add related questions
        response.related_questions = self.generate_related_questions(response)
        
        # Add citations
        response.citations = self.format_citations(response.sources)
        
        return response
```

### Integration with External Systems

```python
# API integration
from flask import Flask, request, jsonify

app = Flask(__name__)
pipeline = RAGChatPipeline()

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    response = pipeline.query(query)
    return jsonify({
        'answer': response.answer,
        'sources': response.sources,
        'metadata': {
            'chunk_count': response.chunk_count,
            'response_time': response.query_time
        }
    })
```

## 🔄 Integration

Module này tích hợp tất cả các modules khác:
- `src/vectorstore/` - Vector database operations
- `src/retriever/` - Similarity search
- `src/llm/` - Text generation
- `src/embedder/` - Query embedding

## 📝 Best Practices

1. **Performance**: Monitor response times và optimize bottlenecks
2. **Quality**: Review retrieved chunks cho relevance
3. **Caching**: Enable query caching cho repeated questions
4. **Monitoring**: Log all queries và responses cho analysis
5. **Error Handling**: Implement graceful degradation

## 🔍 Troubleshooting

### Common Issues

1. **Slow responses**: Check LLM generation time, consider smaller models
2. **Poor answers**: Verify chunk quality và retrieval relevance
3. **Connection errors**: Ensure Ollama is running và accessible
4. **Memory issues**: Monitor vector store size và query complexity

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect intermediate steps
pipeline = RAGChatPipeline()
pipeline.debug_mode = True

response = pipeline.query("What is diabetes?")
# Debug info will show retrieval, context building, generation steps

# Performance profiling
pipeline.profile_query("What is diabetes?")
# Shows timing breakdown for each step
```

## 📋 TODO

- [ ] Add query caching mechanism
- [ ] Implement streaming responses
- [ ] Add conversation memory
- [ ] Support for multiple retrieval strategies
- [ ] Add A/B testing framework
- [ ] Implement query analytics dashboard
- [ ] Add support for multimodal queries
- [ ] Implement response quality scoring
