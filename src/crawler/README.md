# Web Crawler Module - Refactored Architecture

Module này chịu trách nhiệm thu thập dữ liệu từ các nguồn web về tiểu đường với architecture rõ ràng và dễ maintain.

## 🏗️ New Architecture

```
src/crawler/
├── __init__.py              # Main exports
├── impl.py                  # Backward compatibility imports
├── detection.py             # Site detection utilities
├── sites_config.json        # Site-specific configurations
├── configURL.json          # URL list for crawling (main)
├── base/
│   └── __init__.py         # BaseCrawler with HTTP functionality
├── generic/
│   └── __init__.py         # GenericCrawler with config-driven approach
├── legacy/
│   └── __init__.py         # DiabetesCrawler (backward compatibility)
├── components/
│   └── __init__.py         # LinkExtractor, ArticleLink
├── pagination/
│   └── __init__.py         # Pagination strategies (Traditional, AJAX)
├── utils/
│   └── __init__.py         # URL utilities, logging
└── README.md               # Updated documentation
```

## 🎯 Separation of Concerns

### **1. Configuration Files**
- **`configURL.json`**: Main URL list - `crawl_runner.py` reads this to know WHAT to crawl
- **`sites_config.json`**: Site-specific configs - GenericCrawler uses this to know HOW to crawl each site

### **2. Core Components**

#### **BaseCrawler** (`base/`)
- **Responsibility**: HTTP requests, retries, session management
- **Size**: ~200 lines (vs 1000+ before)
- **Features**: Rate limiting, error handling, file saving

#### **GenericCrawler** (`generic/`)
- **Responsibility**: Config-driven multi-site crawling
- **Size**: ~300 lines
- **Features**: Site detection, link discovery, document parsing

#### **DiabetesCrawler** (`legacy/`)
- **Responsibility**: Backward compatibility for yhoccongdong.com
- **Size**: ~400 lines
- **Features**: Legacy logic maintained

#### **LinkExtractor** (`components/`)
- **Responsibility**: Extract article links from HTML
- **Size**: ~150 lines
- **Features**: CSS selectors, category detection, duplicate prevention

#### **Pagination Strategies** (`pagination/`)
- **Responsibility**: Handle different pagination types
- **Size**: ~200 lines total
- **Features**: Traditional pagination, AJAX pagination, factory pattern

#### **Utils** (`utils/`)
- **Responsibility**: Shared utilities
- **Size**: ~100 lines
- **Features**: URL normalization, logging, nonce extraction

### **3. Detection Logic** (`detection.py`)
- **Responsibility**: Site type detection from URLs
- **Size**: ~50 lines
- **Features**: Domain matching, fallback patterns

## 🔄 Data Flow

```
1. crawl_runner.py
   ↓ reads
2. configURL.json (URLs to crawl)
   ↓ detects site type
3. detection.py
   ↓ loads site config
4. sites_config.json (how to crawl)
   ↓ creates appropriate crawler
5. GenericCrawler/DiabetesCrawler
   ↓ uses components
6. LinkExtractor + Pagination
   ↓ processes content
7. BaseCrawler (HTTP + saving)
```

## 🚀 Benefits of Refactoring

### **1. Maintainability**
- **Single Responsibility**: Each module has one clear purpose
- **Small Files**: <300 lines each vs 1000+ line god file
- **Clear Dependencies**: Explicit imports and interfaces

### **2. Testability**
- **Isolated Components**: Easy to unit test each module
- **Mockable Dependencies**: Clear interfaces for mocking
- **Focused Tests**: Test specific functionality per module

### **3. Extensibility**
- **New Sites**: Add to `sites_config.json` only
- **New Pagination**: Add new strategy to `pagination/`
- **New Features**: Add new component without affecting others

### **4. Debugging**
- **Clear Error Sources**: Know which module has issues
- **Focused Logging**: Each module logs with its own name
- **Isolated Testing**: Test components independently

## 📋 Usage Examples

### **Single URL Crawling**
```python
from crawler import GenericCrawler
from crawler.detection import detect_site_type, load_sites_config

# Auto-detect site and create crawler
sites_config = load_sites_config()
site_type = detect_site_type(url, sites_config)
site_config = sites_config['sites'][site_type]

crawler = GenericCrawler(site_config=site_config)
links = crawler.get_article_links(max_pages=3, max_links=50)
```

### **Config-Driven Crawling**
```python
from pipelines.crawl_runner import run_config_mode

# Uses configURL.json + sites_config.json automatically
run_config_mode(config, "data/documents")
```

### **Adding New Site**
```json
// Add to sites_config.json
{
  "sites": {
    "new_site": {
      "base_url": "https://example.com/health/",
      "default_category": "general",
      "selectors": {
        "article_links": ["a.article-link"],
        "category_patterns": {"research": "research"}
      },
      "pagination": {
        "type": "traditional",
        "url_pattern": "{base_url}/page/{page}/"
      }
    }
  }
}
```

## 🔧 Configuration Structure

### **configURL.json** (WHAT to crawl)
```json
{
  "urls": [
    {
      "url": "https://yhoccongdong.com/tieu-duong/",
      "depth": 2,
      "category": "general", 
      "max_article": 50,
      "enabled": true
    }
  ]
}
```

### **sites_config.json** (HOW to crawl)
```json
{
  "sites": {
    "yhoccongdong": {
      "base_url": "https://yhoccongdong.com/tieu-duong/",
      "selectors": {"article_links": ["a.post-title"]},
      "pagination": {"type": "ajax", "ajax": {...}}
    }
  }
}
```

## 🎯 Migration Benefits

### **Before (God File)**
- ❌ 1000+ lines in single file
- ❌ Multiple responsibilities mixed
- ❌ Hard to test and debug
- ❌ Difficult to extend

### **After (Modular)**
- ✅ 8 focused modules (<300 lines each)
- ✅ Clear separation of concerns
- ✅ Easy to test and debug
- ✅ Simple to extend new features

## 📊 Module Sizes

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `base/` | 200 | HTTP handling |
| `generic/` | 300 | Multi-site crawling |
| `legacy/` | 400 | Backward compatibility |
| `components/` | 150 | Link extraction |
| `pagination/` | 200 | Pagination strategies |
| `utils/` | 100 | Shared utilities |
| `detection/` | 50 | Site detection |
| **Total** | **1400** | **Well-organized** |

## 🔒 Backward Compatibility

- **All existing imports work** through `impl.py`
- **DiabetesCrawler** still available in `legacy/`
- **Same API** for existing code
- **Gradual migration** possible

Module crawler giờ đây **sạch, dễ debug, và dễ mở rộng**! 🎉
