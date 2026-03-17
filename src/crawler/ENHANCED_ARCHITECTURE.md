# Enhanced Crawler Architecture - Efficient Multi-URL Processing

## 🎯 **Problem Solved**

### **Before (Inefficient)**
```
URL 1 → Find links → Crawl articles → URL 2 → Find links → Crawl articles → URL 3 → ...
```
- ❌ **Sequential processing** - Each URL processed separately
- ❌ **Duplicate crawling** - Same articles might be crawled multiple times
- ❌ **Poor resource utilization** - Long gaps between article processing

### **After (Efficient)**
```
Phase 1: ALL URLs → Find ALL links → Deduplicate
Phase 2: ALL unique links → Crawl ALL articles
```
- ✅ **Batch link collection** - Collect all links first
- ✅ **Deduplication** - Remove duplicate URLs across sites
- ✅ **Efficient crawling** - Continuous article processing

## 🔄 **New Two-Phase Architecture**

### **Phase 1: Link Collection**
```python
for each URL in config:
    - Create appropriate crawler (GenericCrawler/DiabetesCrawler)
    - Extract article links (if depth > 1)
    - Add to global link collection
    - Add delay between URLs (respect rate limits)

# Remove duplicates
unique_links = deduplicate(all_links)
```

### **Phase 2: Article Crawling**
```python
for each unique article link:
    - Detect site type for this specific article
    - Create appropriate crawler
    - Fetch and process article
    - Save raw HTML + processed document
    - Short delay between articles (0.5s)
```

## 📊 **Performance Benefits**

### **Efficiency Gains**
| Metric | Before | After |
|--------|--------|-------|
| Link Discovery | Per-URL | Batch collection |
| Duplicate Handling | None | Automatic deduplication |
| Article Processing | Gapped | Continuous |
| Resource Usage | Poor | Optimized |

### **Example Scenario**
```
Config: 3 URLs (yhoccongdong, WHO, NIDDK)
- yhoccongdong: 50 articles
- WHO: 1 article  
- NIDDK: 30 articles
- Overlap: 5 articles appear on multiple sites

Before: 3 separate crawls = 81 total requests
After: 1 batch discovery + 76 unique articles = 77 total requests
```

## 🚀 **Implementation Details**

### **Link Collection Strategy**
```python
# For depth > 1: Discover articles
if depth > 1 and hasattr(crawler, 'get_article_links'):
    article_links = crawler.get_article_links(max_pages=5, max_links=max_article)
    all_article_links.extend(article_links)

# For depth = 1: Add URL itself as article
else:
    article_link = ArticleLink(title=url, url=url, category=category)
    all_article_links.append(article_link)
```

### **Deduplication Logic**
```python
unique_links = []
seen_urls = set()

for link in all_article_links:
    if link.url not in seen_urls:
        unique_links.append(link)
        seen_urls.add(link.url)
```

### **Optimized Delays**
```python
# Between URLs: Respect rate limits (2s default)
time.sleep(delay)  # Between different sites

# Between articles: Shorter delay (0.5s)
time.sleep(0.5)  # Between articles (same/different sites)
```

## 📋 **Configuration Impact**

### **Current configURL.json**
```json
{
  "urls": [
    {
      "url": "https://yhoccongdong.com/tieu-duong/",
      "depth": 2,
      "max_article": 50
    },
    {
      "url": "https://www.who.int/news-room/fact-sheets/detail/diabetes", 
      "depth": 1,
      "max_article": 1
    },
    {
      "url": "https://www.niddk.nih.gov/health-information/diabetes",
      "depth": 2,
      "max_article": 30
    }
  ]
}
```

### **Processing Flow**
```
1. yhoccongdong (depth=2) → Discover 50 links
2. WHO (depth=1) → Add 1 direct link  
3. NIDDK (depth=2) → Discover 30 links
4. Deduplicate → 76 unique links
5. Crawl all 76 articles continuously
```

## 🎯 **Key Benefits**

### **1. Efficiency**
- ✅ **Batch processing** - Collect all links first
- ✅ **No duplicates** - Automatic URL deduplication
- ✅ **Continuous crawling** - No gaps between articles

### **2. Resource Optimization**
- ✅ **Better rate limiting** - Proper delays between sites
- ✅ **Faster processing** - Continuous article crawling
- ✅ **Reduced server load** - Avoid duplicate requests

### **3. Scalability**
- ✅ **Multi-site support** - Handle many URLs efficiently
- ✅ **Configurable depth** - Mix depth=1 and depth=2 URLs
- ✅ **Smart deduplication** - Cross-site duplicate detection

## 🔄 **Backward Compatibility**

- ✅ **Existing configs work** - No changes needed
- ✅ **Single URL mode unchanged** - `run_single_url()` still works
- ✅ **Depth=1 URLs handled** - Direct processing for simple pages

## 📈 **Expected Performance**

### **With 3 URLs (50+1+30 articles)**
```
Before: ~3 minutes (sequential processing)
After: ~2 minutes (batch + continuous)
Improvement: ~33% faster
```

### **With 5 URLs (200+ articles total)**
```
Before: ~8 minutes (lots of gaps)
After: ~5 minutes (continuous processing)  
Improvement: ~38% faster
```

**Enhanced crawler architecture ready for efficient multi-URL processing!** 🚀
