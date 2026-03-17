# Text Processing Module

Module này cung cấp các utilities cho việc xử lý và làm sạch văn bản, chuẩn hóa dữ liệu và chia nhỏ tài liệu thành các cấu trúc có ý nghĩa cho hệ thống RAG.

## 🎯 Mục tiêu

- Làm sạch và chuẩn hóa văn bản từ web crawling
- Tách tài liệu thành các sections theo cấu trúc heading
- Cung cấp text normalization cho consistent processing
- Support chunking operations với proper text preparation
- Handle various text formats và edge cases

## 🏗️ Kiến trúc

```
src/processors/
├── __init__.py
├── cleaner.py          # HTML content cleaning
├── normalizer.py       # Text normalization
├── query_cleaner.py    # Query text cleaning
├── section_splitter.py # Section-aware text splitting
└── README.md          # This file
```

## 🔧 Components

### HTML Cleaner (`cleaner.py`)

Làm sạch HTML content bằng cách loại bỏ boilerplate elements:

```python
def clean_article_soup(soup: BeautifulSoup) -> None:
    """
    Remove boilerplate elements:
    - script, style
    - nav, footer, header  
    - sidebars, related posts, comments
    - share buttons, keyword blocks
    """
```

**Features:**
- Remove navigation và footer elements
- Clean sidebars và related content
- Remove comments và share buttons
- Preserve main article content

### Text Normalizer (`normalizer.py`)

Chuẩn hóa Unicode và whitespace:

```python
def normalize_text(text: str) -> str:
    """
    Normalize text according to project spec:
    - Unicode NFC normalization
    - Replace non-breaking spaces
    - Collapse multiple spaces/newlines
    - Strip leading/trailing whitespace
    """
```

**Features:**
- Unicode NFC normalization
- Whitespace normalization
- Consistent line endings
- Empty content handling

### Section Splitter (`section_splitter.py`)

Tách content thành sections dựa trên heading hierarchy:

```python
def split_sections(container: Tag) -> List[Dict[str, str]]:
    """
    Split content preserving h1/h2/h3 hierarchy:
    - h1: document title level
    - h2: major sections
    - h3: subsections
    - p/ul/ol: assigned to nearest heading
    """
```

**Features:**
- Preserve document structure
- Handle nested headings
- Group content under proper headings
- Normalize section content

### Query Cleaner (`query_cleaner.py`)

Làm sạch user queries:

```python
def clean_query(query: str) -> str:
    """Clean and normalize user query text."""
```

### Document Chunker (`chunker.py`)

Placeholder cho advanced chunking operations:

```python
class DocumentChunker:
    """Advanced document chunking with LangChain integration."""
```

## 🚀 Usage

### HTML Content Cleaning

```python
from bs4 import BeautifulSoup
from src.processors.cleaner import clean_article_soup

# Parse HTML
html = "<html>...</html>"
soup = BeautifulSoup(html, 'html.parser')

# Clean content
clean_article_soup(soup)

# Extract clean text
clean_text = soup.get_text()
```

### Text Normalization

```python
from src.processors.normalizer import normalize_text

# Normalize various text formats
messy_text = "Diabetes  is  a   chronic\n\n\ncondition"
clean_text = normalize_text(messy_text)
print(clean_text)  # "Diabetes is a chronic condition"

# Handle Unicode
unicode_text = "Diabetes\u00a0symptoms"  # Non-breaking space
clean_text = normalize_text(unicode_text)
print(clean_text)  # "Diabetes symptoms"
```

### Section Splitting

```python
from bs4 import BeautifulSoup
from src.processors.section_splitter import split_sections

# Parse HTML with headings
html = """
<h1>Diabetes Overview</h1>
<p>Introduction to diabetes...</p>
<h2>Symptoms</h2>
<p>Common symptoms include...</p>
<h3>Type 1 Symptoms</h3>
<p>Specific to type 1...</p>
"""

soup = BeautifulSoup(html, 'html.parser')
sections = split_sections(soup)

for section in sections:
    print(f"Heading: {section['heading']}")
    print(f"Content: {section['content'][:50]}...")
    print("---")
```

### Complete Processing Pipeline

```python
from bs4 import BeautifulSoup
from src.processors import (
    clean_article_soup, 
    normalize_text, 
    split_sections
)

def process_html_content(html: str) -> List[Dict]:
    """Complete HTML processing pipeline."""
    
    # Parse and clean HTML
    soup = BeautifulSoup(html, 'html.parser')
    clean_article_soup(soup)
    
    # Split into sections
    sections = split_sections(soup)
    
    # Normalize content
    for section in sections:
        section['content'] = normalize_text(section['content'])
        section['heading'] = normalize_text(section['heading'])
    
    return sections

# Usage
html_content = "<html>...</html>"
processed_sections = process_html_content(html_content)
```

## 📊 Data Flow

### Processing Pipeline

```
Raw HTML → Clean HTML → Extract Sections → Normalize Text → Ready for Chunking
```

### Input/Output Examples

**Input HTML:**
```html
<html>
<head><title>Diabetes Guide</title></head>
<body>
<nav>Navigation...</nav>
<h1>Understanding Diabetes</h1>
<p>Diabetes is a metabolic disorder...</p>
<div class="sidebar">Related articles...</div>
<h2>Types of Diabetes</h2>
<p>There are several types...</p>
</body>
</html>
```

**Output Sections:**
```python
[
    {
        "heading": "Understanding Diabetes",
        "content": "Diabetes is a metabolic disorder..."
    },
    {
        "heading": "Types of Diabetes", 
        "content": "There are several types..."
    }
]
```

## ⚙️ Configuration

### Cleaning Selectors

Customize cleaning rules trong `cleaner.py`:

```python
selectors = [
    ".sidebar",
    "[class*='sidebar']",
    "[id*='sidebar']",
    ".related-posts",
    ".comments",
    # Add custom selectors
]
```

### Normalization Rules

Adjust normalization trong `normalizer.py`:

```python
# Custom whitespace handling
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")  # Allow double newlines
```

### Section Splitting Rules

Configure heading hierarchy trong `section_splitter.py`:

```python
# Support h4 headings
if name in ("h1", "h2", "h3", "h4"):
    # Handle h4 as subsection
```

## 🧪 Testing

```bash
# Run processor tests
python -m pytest tests/test_processors.py

# Test individual components
python -c "
from src.processors.normalizer import normalize_text
print(normalize_text('  Multiple   spaces  '))
"

# Test HTML cleaning
python -c "
from bs4 import BeautifulSoup
from src.processors.cleaner import clean_article_soup
html = '<html><body><div class=\"sidebar\">Ads</div><p>Content</p></body></html>'
soup = BeautifulSoup(html, 'html.parser')
clean_article_soup(soup)
print(soup.get_text())
"
```

## 🔧 Customization

### Custom Cleaning Rules

```python
def custom_cleaner(soup: BeautifulSoup) -> None:
    """Custom cleaning logic."""
    # Remove specific elements
    for tag in soup.find_all(class_='advertisement'):
        tag.decompose()
    
    # Clean specific attributes
    for tag in soup.find_all():
        tag.attrs = {k: v for k, v in tag.attrs.items() 
                    if k not in ['onclick', 'style']}
```

### Custom Section Splitting

```python
def custom_section_splitter(container: Tag) -> List[Dict]:
    """Custom section splitting logic."""
    sections = []
    
    # Custom logic for specific content types
    for element in container.find_all(['h1', 'h2', 'h3']):
        # Custom section extraction
        pass
    
    return sections
```

### Domain-Specific Processing

```python
def medical_content_processor(html: str) -> List[Dict]:
    """Specialized processor for medical content."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Medical-specific cleaning
    clean_article_soup(soup)
    
    # Preserve medical terminology
    for term in soup.find_all(class_='medical-term'):
        term['data-medical'] = 'true'
    
    # Extract sections
    sections = split_sections(soup)
    
    # Medical content validation
    validated_sections = []
    for section in sections:
        if is_medical_content(section['content']):
            validated_sections.append(section)
    
    return validated_sections
```

## 🔄 Integration

Module này được sử dụng bởi:
- `src/crawler/` - Clean crawled HTML content
- `src/chunking/` - Prepare text for chunking
- `src/pipelines/` - Text preprocessing pipeline

## 📝 Best Practices

1. **Content Preservation**: Ensure important content isn't over-cleaned
2. **Structure Maintenance**: Preserve document hierarchy and relationships
3. **Medical Terminology**: Handle medical terms carefully
4. **Unicode Handling**: Properly handle special characters and symbols
5. **Performance**: Optimize for processing large documents

## 🔍 Troubleshooting

### Common Issues

1. **Over-cleaning**: Too much content removed - adjust selectors
2. **Lost structure**: Headings not preserved - check splitting logic
3. **Encoding issues**: Unicode problems - verify normalization
4. **Empty sections**: Content lost during cleaning - review rules

### Debug Tools

```python
# Inspect cleaning process
from bs4 import BeautifulSoup
from src.processors.cleaner import clean_article_soup

html = "<html>...</html>"
soup = BeautifulSoup(html, 'html.parser')
print("Before cleaning:", len(soup.get_text()))
clean_article_soup(soup)
print("After cleaning:", len(soup.get_text()))

# Test normalization
from src.processors.normalizer import normalize_text
test_cases = [
    "Multiple   spaces",
    "Unicode\u00a0test",
    "Line\n\n\nbreaks"
]
for text in test_cases:
    print(f"'{text}' -> '{normalize_text(text)}'")
```

## 📋 TODO

- [ ] Implement advanced chunking trong `chunker.py`
- [ ] Add language detection và language-specific processing
- [ ] Implement content quality scoring
- [ ] Add support for table extraction
- [ ] Implement medical entity recognition
- [ ] Add content deduplication
- [ ] Support for PDF document processing
- [ ] Add content validation rules
