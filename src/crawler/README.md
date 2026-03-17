# Web Crawler Module - Proper Python Package Architecture

Module này chịu trách nhiệm thu thập dữ liệu từ các nguồn web về tiểu đường với proper Python package design và clear separation of concerns.

## 🏗️ Final Architecture

```
src/crawler/
├── __init__.py              # Package exports only (25 lines)
├── impl.py                  # Backward compatibility imports (20 lines)
├── detection.py             # Site detection utilities
├── scraper.py               # Convenience functions
├── base.py                  # BaseCrawler with HTTP functionality (150 lines)
├── generic.py               # GenericCrawler with config-driven approach (120 lines)
├── legacy.py                # DiabetesCrawler for backward compatibility (200 lines)
├── config/                  # Configuration files
│   ├── configURL.json      # URL list for crawling (WHAT to crawl)
│   └── sites_config.json    # Site-specific configurations (HOW to crawl)
├── components/
│   ├── __init__.py          # Component exports (5 lines)
│   ├── links.py             # LinkExtractor & ArticleLink (150 lines)
│   └── parser.py            # DocumentParser for HTML processing (120 lines)
├── pagination/
│   ├── __init__.py          # Pagination exports (5 lines)
│   ├── strategies.py        # TraditionalPagination & AjaxPagination (180 lines)
│   └── factory.py           # PaginationFactory (20 lines)
└── utils/
    ├── __init__.py          # Utility exports (5 lines)
    ├── url.py                # URL utilities (80 lines)
    └── logging.py           # Logging configuration (15 lines)
```

## 🎯 Proper Python Package Design

### **✅ Fixed Issues**
- **No business logic in `__init__.py`** - Only exports and `__all__`
- **Clear file responsibilities** - Each file has single purpose
- **Focused module sizes** - 50-200 lines per file (vs 1000+ god files)
- **Predictable imports** - No hidden logic in import paths

### **📁 Configuration Organization**
```
src/crawler/config/
├── configURL.json      # WHAT to crawl - URL list for crawl_runner.py
└── sites_config.json    # HOW to crawl - Site-specific configs for GenericCrawler
```

## 🔄 Data Flow & Storage

### **Crawling Process**
```
1. Fetch HTML → Save to data/raw/
2. Process with processors module → Save to data/documents/
3. Link raw HTML file in document metadata
```

### **Directory Structure**
```
data/
├── raw/                   # Original HTML files
│   ├── who_int_news-room_fact-sheets_detail_diabetes.html
│   ├── yhoccongdong_com_tieu-duong.html
│   └── niddk_nih_gov_health_information_diabetes.html
└── documents/             # Processed JSON documents
    ├── who_int_news-room_fact-sheets_detail_diabetes.json
    ├── yhoccongdong_com_tieu-duong.json
    └── niddk_nih_gov_health_information_diabetes.json
```

### **Document Metadata**
```json
{
  "doc_id": "who_int_news-room_fact-sheets_detail_diabetes",
  "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
  "title": "Diabetes",
  "sections": [...],
  "metadata": {
    "crawl_time": "2026-03-17T14:30:00Z",
    "source_url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
    "crawler_type": "config_runner",
    "raw_html_file": "data/raw/who_int_news-room_fact-sheets_detail_diabetes.html"
  }
}
```

## 🚀 Usage Examples

### **Basic Usage**
```python
# Clean imports - no hidden logic
from crawler.generic import GenericCrawler
from crawler.detection import detect_site_type, load_sites_config

# Auto-detect and crawl
sites_config = load_sites_config()  # Uses src/crawler/config/sites_config.json
site_type = detect_site_type(url, sites_config)
site_config = sites_config['sites'][site_type]
crawler = GenericCrawler(site_config=site_config)
links = crawler.get_article_links(max_pages=5, max_links=50)
```

### **Pipeline Usage**
```python
from pipelines.crawl_runner import run_single_url, run_config_mode

# Single URL - saves raw HTML + processed document
run_single_url(
    url="https://www.who.int/news-room/fact-sheets/detail/diabetes",
    output_dir="data/documents"  # Processed docs
)

# Config mode - uses src/crawler/config/configURL.json
run_config_mode(config, "data/documents")
```

### **Convenience Functions**
```python
from crawler.scraper import quick_crawl_all

# One-liner crawling with proper storage
results = quick_crawl_all()
# Creates: data/raw/*.html + data/documents/*.json
```

## 📋 Configuration Files

### **configURL.json** (WHAT to crawl)
```json
{
  "urls": [
    {
      "url": "https://yhoccongdong.com/tieu-duong/",
      "depth": 2,
      "category": "general",
      "max_article": 50,
      "enabled": true,
      "description": "Main diabetes information page"
    },
    {
      "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
      "depth": 1,
      "category": "concepts",
      "max_article": 1,
      "enabled": true,
      "description": "Diabetes concepts and facts"
    }
  ],
  "global_settings": {
    "default_depth": 2,
    "default_category": "general",
    "default_max_article": 50,
    "request_delay_seconds": 2.0,
    "max_retries": 3,
    "timeout_seconds": 30
  }
}
```

### **sites_config.json** (HOW to crawl)
```json
{
  "sites": {
    "yhoccongdong": {
      "base_url": "https://yhoccongdong.com/tieu-duong/",
      "default_category": "general",
      "selectors": {
        "article_links": [
          "a.col-12.post-item_content-title",
          "div.post-item_content a"
        ],
        "category_patterns": {
          "dau-hieu": "symptoms",
          "song-chung": "lifestyle"
        }
      },
      "pagination": {
        "type": "ajax",
        "ajax": {
          "button_selector": "button.btn.button-post-more",
          "ajax_url": "https://yhoccongdong.com/tieu-duong/wp-admin/admin-ajax.php",
          "action": "load_more_posts"
        }
      }
    },
    "who": {
      "base_url": "https://www.who.int",
      "default_category": "concepts",
      "selectors": {
        "article_links": [
          "a.sf-list-vertical__item",
          "a[href*='/news-room/fact-sheets/detail']"
        ]
      },
      "pagination": {
        "type": "traditional"
      }
    }
  },
  "global_settings": {
    "default_delay": 2.0,
    "default_max_retries": 3,
    "default_timeout": 30.0
  }
}
```

## 🔧 Module Responsibilities

### **Core Files**
- **`base.py`**: HTTP requests, retries, session management, file saving
- **`generic.py`**: Config-driven multi-site crawling, site detection
- **`legacy.py`**: Backward compatibility for yhoccongdong.com

### **Components**
- **`components/links.py`**: Link extraction, CSS selectors, duplicate prevention
- **`components/parser.py`**: Document parsing, HTML cleaning, section extraction

### **Pagination**
- **`pagination/strategies.py`**: Traditional and AJAX pagination implementations
- **`pagination/factory.py`**: Strategy factory pattern

### **Utils**
- **`utils/url.py`**: URL normalization, slug generation, nonce extraction
- **`utils/logging.py`**: Logging configuration

## 🎯 Benefits of Proper Architecture

### **1. Python Best Practices**
- ✅ **Clean `__init__.py`** - Only exports, no business logic
- ✅ **Single responsibility** - Each file has one clear purpose
- ✅ **Proper imports** - Predictable, no hidden logic
- ✅ **Focused modules** - 50-200 lines per file

### **2. Maintainability**
- ✅ **Easy debugging** - Know exactly which file to look at
- ✅ **Clear dependencies** - Explicit imports and interfaces
- ✅ **Modular testing** - Test each component independently
- ✅ **Simple extension** - Add features without touching core

### **3. Data Organization**
- ✅ **Separate storage** - Raw HTML vs processed documents
- ✅ **Traceable metadata** - Link to original raw file
- ✅ **Centralized config** - All configs in `config/` folder
- ✅ **Clear paths** - Predictable file organization

### **4. Developer Experience**
- ✅ **IDE friendly** - Proper module recognition
- ✅ **Clear documentation** - Each module documented
- ✅ **Backward compatible** - Existing code still works
- ✅ **Easy onboarding** - Clear structure for new developers

## 📊 Architecture Metrics

| Metric | Before | After |
|--------|--------|-------|
| `__init__.py` lines | 500+ (business logic) | 45 (exports only) |
| Largest file | 1000+ lines | 200 lines |
| Number of files | 8 modules | 12 focused files |
| Config organization | Scattered | Centralized in `config/` |
| Data storage | Mixed | Separated (raw vs processed) |

## 🔒 Backward Compatibility

All existing imports continue to work:
```python
# These still work
from crawler import BaseCrawler, GenericCrawler, DiabetesCrawler
from crawler.impl import BaseCrawler  # Legacy path
from crawler.scraper import quick_crawl_yhoccongdong
```

## 🚀 Quick Start

```bash
# Install dependencies (if needed)
pip install requests beautifulsoup4

# Run with config mode
python -m src.pipelines.crawl_runner

# Run single URL
python -m src.pipelines.crawl_runner --url https://www.who.int/news-room/fact-sheets/detail/diabetes

# Check output
ls data/raw/      # Original HTML files
ls data/documents/ # Processed JSON documents
```

Module crawler giờ đây follows proper Python package design với clean separation of concerns, proper data organization, và maintainable architecture! 🎉
