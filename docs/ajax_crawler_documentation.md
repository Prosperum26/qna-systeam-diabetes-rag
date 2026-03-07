# AJAX-Based Diabetes Crawler

## Overview

The diabetes crawler has been updated to support AJAX-based pagination for WordPress sites that use "Load More" functionality instead of traditional pagination.

## Key Features

### 1. Dual Pagination Support
- **AJAX Pagination** (default): Uses WordPress admin-ajax.php endpoint
- **Traditional Pagination**: Falls back to URL-based pagination (`/page/N/`)

### 2. Automatic Nonce Extraction
- Extracts AJAX nonce from JavaScript variables in the initial page
- Supports multiple nonce patterns used by WordPress themes

### 3. Robust Article Parsing
- Handles both initial page HTML and AJAX response HTML
- Supports JSON responses with `html` or `data` fields
- Falls back to plain text responses

## Usage

### Basic Usage (AJAX enabled by default)

```python
from src.crawler.scraper import run_diabetes_crawler

# Crawl 10 articles using AJAX pagination
run_diabetes_crawler(max_articles=10, base_dir="data")
```

### Advanced Usage

```python
from src.crawler.impl import DiabetesCrawler

# Create crawler instance
crawler = DiabetesCrawler(delay_seconds=2.0)

# Get article links using AJAX
links = crawler.get_article_links(max_pages=5, max_links=20, use_ajax=True)

# Or use traditional pagination
links = crawler.get_article_links(max_pages=5, max_links=20, use_ajax=False)

# Full crawl with AJAX
crawler.crawl(max_articles=10, base_dir="data", use_ajax=True)
```

## AJAX Implementation Details

### 1. AJAX Endpoint
- URL: `https://yhoccongdong.com/tieu-duong/wp-admin/admin-ajax.php`
- Method: POST
- Content-Type: `application/x-www-form-urlencoded`

### 2. Request Parameters
```json
{
    "action": "watch_more_ar",
    "page": "1",
    "view": "cancer-default",
    "_ajax_nonce": "[extracted_nonce]"
}
```

### 3. Response Handling
- **JSON Response**: Extracts HTML from `html` or `data` fields
- **Plain Text**: Uses raw text response
- **Error Handling**: Logs status codes and retries

### 4. Nonce Extraction Patterns
The crawler searches for nonce values using these regex patterns:
- `nonce["']?\s*:\s*["']([a-f0-9]+)["']`
- `_ajax_nonce["']?\s*:\s*["']([a-f0-9]+)["']`
- `nonce_ajax["']?\s*=\s*{[^}]*nonce["']?\s*:\s*["']([a-f0-9]+)["']`

## Article Structure

### HTML Structure
```html
<div class="post-item">
    <div class="post-item_content">
        <a class="post-item_content-title" href="ARTICLE_URL">
            <h4>ARTICLE_TITLE</h4>
        </a>
    </div>
</div>
```

### CSS Selectors Used
- Primary: `a.col-12.post-item_content-title`
- Fallback 1: `div.post-item_content a`
- Fallback 2: `.post-item a`

## Error Handling

### 1. Network Errors
- Automatic retries with exponential backoff
- Respect delay settings between requests
- Timeout handling

### 2. Parsing Errors
- Graceful fallback between selectors
- Duplicate detection and removal
- Content validation

### 3. AJAX-Specific Errors
- Nonce extraction failures
- Invalid JSON responses
- HTTP error status codes

## Testing

Run the test script to verify AJAX functionality:

```bash
python tests/test_ajax_crawler.py
```

This will:
1. Test AJAX link discovery
2. Compare with traditional pagination
3. Perform a small full crawl
4. Save results to `test_data` directory

## Configuration Options

### DiabetesCrawler Parameters
- `delay_seconds`: Delay between requests (default: 1.5)
- `max_retries`: Maximum retry attempts (default: 3)
- `timeout_seconds`: Request timeout (default: 15.0)

### Method Parameters
- `use_ajax`: Enable/disable AJAX pagination (default: True)
- `max_pages`: Maximum pages to fetch
- `max_links`: Maximum links to discover
- `max_articles`: Maximum articles to process

## Troubleshooting

### Common Issues

1. **Nonce not found**
   - Check if the website structure has changed
   - Verify the nonce extraction patterns
   - Manual inspection of the page source

2. **AJAX requests failing**
   - Verify the AJAX endpoint URL
   - Check request parameters
   - Inspect network requests in browser dev tools

3. **No articles found**
   - Verify CSS selectors match current site structure
   - Check if site requires authentication
   - Validate URL patterns

### Debug Mode
Enable debug logging for detailed information:

```python
import logging
configure_logging(logging.DEBUG)
```

## Migration from Traditional Pagination

Existing code will continue to work with `use_ajax=False`:

```python
# Old behavior (traditional pagination)
crawler.crawl(max_articles=10, use_ajax=False)

# New behavior (AJAX pagination - default)
crawler.crawl(max_articles=10)  # use_ajax=True by default
```

## Performance Considerations

- AJAX pagination is typically faster than traditional pagination
- Fewer HTTP requests needed
- Reduced bandwidth usage
- Better for sites with large article collections

## Security Notes

- Respects robots.txt and rate limits
- Uses appropriate User-Agent headers
- Handles sensitive data (nonces) securely
- No authentication bypass attempts
