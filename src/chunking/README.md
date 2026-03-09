# Text Chunking Module

Module này chịu trách nhiệm chia nhỏ các tài liệu văn bản dài thành các đoạn (chunks) có kích thước phù hợp cho việc embedding và retrieval trong hệ thống RAG.

## 🎯 Mục tiêu

- Chia nhỏ văn bản medical content thành các đoạn có ý nghĩa ngữ cảnh
- Giữ nguyên cấu trúc section và heading của tài liệu
- Tối ưu cho việc tìm kiếm tương đồng và generation
- Hỗ trợ multiple chunking strategies cho different content types

## 🏗️ Kiến trúc

```
src/chunking/
├── __init__.py
├── chunker.py          # Main chunker implementation
├── rules.py            # Chunking rules and utilities
├── token_counter.py    # Token counting utilities
└── README.md          # This file
```

## 🔧 Components

### HybridChunker (`chunker.py`)

Class chính kết hợp multiple strategies:

```python
@dataclass
class HybridChunker:
    token_counter: TokenCounter
    max_tokens_per_chunk: int = 450
    chunk_size: int = 400
    overlap: int = 60
    min_section_tokens: int = 120
```

**Features:**
- Section-aware chunking: Giữ nguyên cấu trúc sections
- Sliding window: Overlap giữa các chunks để maintain context
- Token-based sizing: Đảm bảo chunks không quá dài cho model
- List preservation: Không chia ngang list items

### Chunking Rules (`rules.py`)

Utilities cho text processing:

- **`split_into_units()`**: Chia content thành logical units
- **`merge_small_sections()`**: Gộp các sections quá nhỏ
- **`is_list_like()`**: Detect list items để preserve structure

### Token Counter (`token_counter.py`)

Đếm tokens để đảm bảo chunks phù hợp với model limits.

## 🚀 Usage

```python
from src.chunking.chunker import HybridChunker
from src.chunking.token_counter import TokenCounter

# Initialize chunker
token_counter = TokenCounter()
chunker = HybridChunker(
    token_counter=token_counter,
    max_tokens_per_chunk=450,
    overlap=60
)

# Chunk document
document = {
    "doc_id": "doc_001",
    "title": "Diabetes Overview",
    "sections": [
        {"heading": "Introduction", "content": "..."},
        {"heading": "Symptoms", "content": "..."}
    ]
}

chunks = chunker.chunk_document(document)
```

## 📊 Chunking Strategy

### 1. Section-Aware Processing
- Tách document theo sections tự nhiên
- Merge các sections quá nhỏ (<120 tokens)
- Preserve heading information trong metadata

### 2. Logical Unit Splitting
- Split content thành units dựa trên newlines
- Merge consecutive list items
- Preserve structure của bullet points và numbered lists

### 3. Sliding Window with Overlap
- Chia sections thành chunks với overlap 60 tokens
- Đảm bảo context continuity giữa các chunks
- Respect max token limits (450 tokens/chunk)

### 4. Metadata Enrichment
Mỗi chunk chứa metadata:
- `chunk_id`: Unique identifier
- `doc_id`: Source document ID
- `title`: Document title
- `heading`: Section heading
- `content`: Chunk content
- `position`: Position trong document
- `token_count`: Số tokens trong chunk

## ⚙️ Configuration

Parameters trong `HybridChunker`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tokens_per_chunk` | 450 | Maximum tokens per chunk |
| `chunk_size` | 400 | Target chunk size |
| `overlap` | 60 | Overlap between chunks |
| `min_section_tokens` | 120 | Minimum tokens to keep section separate |

## 🔍 Examples

### Medical Document Chunking

**Input:**
```markdown
# Diabetes Mellitus

## Types
Type 1 diabetes is an autoimmune condition...
Type 2 diabetes is characterized by insulin resistance...

## Symptoms
Common symptoms include:
- Increased thirst
- Frequent urination
- Unexplained weight loss
```

**Output Chunks:**
```python
[
    {
        "chunk_id": "doc_001_chunk_0",
        "content": "Diabetes Mellitus\n\nTypes\nType 1 diabetes is an autoimmune condition...",
        "heading": "Types",
        "token_count": 45
    },
    {
        "chunk_id": "doc_001_chunk_1", 
        "content": "Type 2 diabetes is characterized by insulin resistance...\n\nSymptoms\nCommon symptoms include:\n- Increased thirst",
        "heading": "Symptoms",
        "token_count": 42
    }
]
```

## 🧪 Testing

```bash
# Run chunking tests
python -m pytest tests/test_chunking.py

# Test with sample data
python -c "
from src.chunking.chunker import HybridChunker
from src.chunking.token_counter import TokenCounter

chunker = HybridChunker(TokenCounter())
# Test with your document
"
```

## 🚧 Performance Considerations

- **Memory**: Chunking là memory-intensive cho large documents
- **Speed**: ~1-2ms per chunk cho average medical content
- **Quality**: Overlap giúp maintain context nhưng tăng storage

## 🔄 Integration

Module này được sử dụng bởi:
- `src/pipelines/chat_pipeline.py` - Main processing pipeline
- `src/rag/pipeline.py` - RAG operations

## 🛠️ Extending

### Adding New Chunking Strategies

1. Implement new chunker class kế thừ từ base interface
2. Add configuration options trong `config.py`
3. Register trong chunking factory

### Custom Rules

Add new rules trong `rules.py`:
```python
def custom_split_rule(content: str) -> List[str]:
    # Your custom logic
    return units
```

## 📝 Best Practices

1. **Medical Content**: Preserve medical terminology và drug names
2. **Context**: Maintain adequate overlap cho complex topics
3. **Structure**: Keep headings và subheadings với content
4. **Tokens**: Monitor token counts để avoid model limits
5. **Quality**: Review chunks cho semantic completeness

## 🔍 Troubleshooting

### Common Issues

1. **Chunks too long**: Giảm `max_tokens_per_chunk`
2. **Lost context**: Tăng `overlap` parameter
3. **Broken lists**: Check `is_list_like()` logic
4. **Poor retrieval**: Adjust chunking strategy cho content type

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect chunks
for chunk in chunks:
    print(f"Chunk {chunk['chunk_id']}: {chunk['token_count']} tokens")
    print(f"Heading: {chunk['heading']}")
    print(f"Content preview: {chunk['content'][:100]}...")
```
