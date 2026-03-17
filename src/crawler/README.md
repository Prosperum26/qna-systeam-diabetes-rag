# Web Crawler Module

Module này chịu trách nhiệm thu thập dữ liệu từ các nguồn web về tiểu đường, trích xuất nội dung và cấu trúc hóa cho việc xử lý tiếp theo trong hệ thống RAG.

## 🎯 Mục tiêu

- Crawl dữ liệu từ các medical websites về tiểu đường
- Extract và làm sạch nội dung bài viết
- Preserve cấu trúc document (headings, sections)
- Handle rate limiting và error recovery
- Save dữ liệu đã crawl theo cấu trúc có tổ chức

## 🏗️ Kiến trúc

```
src/crawler/
├── __init__.py
├── impl.py             # Core crawler implementation
├── scraper.py          # Entry point và convenience functions
└── README.md          # This file
```

## 🔧 Components

### BaseCrawler (`impl.py`)

Base class cung cấp core crawling functionality:

```python
class BaseCrawler:
    def __init__(
        self,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    )
```

**Features:**
- Rate limiting với configurable delays
- Retry mechanism cho failed requests
- Custom User-Agent headers
- Session management
- Comprehensive logging

### DiabetesCrawler (`impl.py`)

Specialized crawler cho diabetes-related content:

```python
class DiabetesCrawler(BaseCrawler):
    def crawl(self, max_articles: int = 5, base_dir: str = "data")
    def discover_article_links(self) -> List[ArticleLink]
    def extract_article_content(self, url: str) -> Optional[Dict]
```

**Features:**
- Target specific diabetes medical websites
- Extract article metadata (title, category, URL)
- Parse và structure content with BeautifulSoup
- Save articles với proper naming convention

### ArticleLink Data Structure

```python
@dataclass
class ArticleLink:
    title: str
    url: str
    category: str
```

## 🚀 Usage

### Basic Usage

```python
from src.crawler.scraper import run_diabetes_crawler

# Crawl 10 articles
run_diabetes_crawler(max_articles=10, base_dir="data")
```

### Advanced Usage

```python
from src.crawler.impl import DiabetesCrawler

crawler = DiabetesCrawler(
    delay_seconds=2.0,
    max_retries=5,
    timeout_seconds=20.0
)

# Discover available articles
links = crawler.discover_article_links()
print(f"Found {len(links)} articles")

# Crawl specific number
crawler.crawl(max_articles=20, base_dir="custom_data")
```

## 📊 Data Structure

### Input Article Format

```python
article = {
    "doc_id": "diabetes_article_001",
    "title": "Understanding Type 2 Diabetes",
    "url": "https://example.com/diabetes-type2",
    "category": "Type 2 Diabetes",
    "content": "Full article content...",
    "sections": [
        {
            "heading": "Overview",
            "content": "Section content..."
        },
        {
            "heading": "Symptoms", 
            "content": "Symptoms content..."
        }
    ],
    "crawl_timestamp": "2024-01-15T10:30:00Z",
    "source": "medical_website"
}
```

### Output Directory Structure

```
data/
└── raw/
    ├── diabetes_article_001.json
    ├── diabetes_article_002.json
    └── ...
```

## ⚙️ Configuration

### Crawler Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `delay_seconds` | 1.5 | Delay between requests |
| `max_retries` | 3 | Maximum retry attempts |
| `timeout_seconds` | 15.0 | Request timeout |
| `max_articles` | 5 | Maximum articles to crawl |
| `base_dir` | "data" | Base directory for output |

### Target Websites

Crawler được cấu hình cho các diabetes medical websites:
- CDC Diabetes pages
- Mayo Clinic Diabetes
- WebMD Diabetes
- American Diabetes Association

## 🔍 Content Extraction

### HTML Processing

1. **Content Cleaning**: Remove ads, navigation, footer
2. **Structure Preservation**: Keep headings, paragraphs, lists
3. **Text Normalization**: Clean whitespace và special characters
4. **Section Splitting**: Split content thành logical sections

### Section Detection

```python
sections = split_sections(clean_content)
# Returns:
[
    {"heading": "Introduction", "content": "..."},
    {"heading": "Symptoms", "content": "..."},
    {"heading": "Treatment", "content": "..."}
]
```

## 🛡️ Error Handling

### Retry Strategy

- **Network errors**: Retry với exponential backoff
- **Timeout errors**: Increase timeout và retry
- **HTTP errors**: Log và skip problematic URLs
- **Parse errors**: Save raw HTML cho debugging

### Logging

```python
# Configure logging
import logging
from src.crawler.impl import configure_logging

configure_logging(logging.INFO)
# Logs crawler progress, errors, and statistics
```

## 📈 Performance Metrics

### Typical Performance

- **Crawling speed**: ~1 article per 2-3 seconds
- **Success rate**: 85-95% cho medical websites
- **Data quality**: High-quality structured content
- **Resource usage**: Low memory footprint

### Monitoring

```python
# Track crawling progress
for i, article in enumerate(crawled_articles, 1):
    print(f"Crawled {i}/{max_articles}: {article['title']}")
```

## 🧪 Testing

```bash
# Run crawler tests
python -m pytest tests/test_crawler.py

# Test with small dataset
python -c "
from src.crawler.impl import DiabetesCrawler
crawler = DiabetesCrawler()
links = crawler.discover_article_links()
print(f'Found {len(links)} articles')
"
```

## 🔧 Customization

### Adding New Websites

1. Implement custom `discover_*_links()` method
2. Add website-specific content extraction logic
3. Configure rate limiting cho new domain

```python
def discover_custom_links(self) -> List[ArticleLink]:
    # Custom discovery logic
    soup = BeautifulSoup(self.fetch(base_url), 'html.parser')
    # Extract links
    return links
```

### Custom Content Extraction

```python
def extract_custom_content(self, url: str) -> Optional[Dict]:
    html = self.fetch(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    # Custom extraction logic
    return article_dict
```

## 🔄 Integration

Module này được sử dụng bởi:
- `main.py` - CLI crawl command
- `src/pipelines/chat_pipeline.py` - Data ingestion pipeline

## 📝 Best Practices

1. **Rate Limiting**: Respect website robots.txt và rate limits
2. **Error Recovery**: Implement robust retry mechanisms
3. **Data Quality**: Validate extracted content trước khi lưu
4. **Storage**: Use structured format (JSON) cho downstream processing
5. **Monitoring**: Log crawling statistics và errors

## 🔍 Troubleshooting

### Common Issues

1. **403 Forbidden**: Check User-Agent headers
2. **Rate Limited**: Increase `delay_seconds`
3. **Parse Errors**: Validate HTML structure
4. **Empty Content**: Check content extraction logic

### Debug Tools

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Inspect raw HTML
html = crawler.fetch(url)
print(html[:500])  # Preview first 500 chars

# Test extraction
article = crawler.extract_article_content(url)
print(f"Extracted {len(article.get('sections', []))} sections")
```

## 📋 TODO

- [ ] Add support for JavaScript-rendered pages (Selenium)
- [ ] Implement incremental crawling (only new articles)
- [ ] Add content deduplication
- [ ] Support for authenticated medical databases
- [ ] Add crawling scheduling functionality
