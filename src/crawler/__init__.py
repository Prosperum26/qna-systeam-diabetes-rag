"""Web crawler module for multi-site data extraction.

This package provides a flexible, config-driven crawler system for RAG pipelines.
Supports multiple websites with different pagination and content extraction strategies.

Main Components:
- BaseCrawler: Core HTTP functionality
- GenericCrawler: Config-driven multi-site crawling
- DiabetesCrawler: Legacy crawler for backward compatibility
- Detection: Automatic site type detection
- Components: Link extraction and document parsing
- Pagination: Traditional and AJAX pagination strategies
- Utils: Shared utilities for URLs and logging

Quick Start:
    from crawler import GenericCrawler, load_sites_config, detect_site_type
    
    # Auto-detect and crawl
    sites_config = load_sites_config()
    site_type = detect_site_type(url, sites_config)
    site_config = sites_config['sites'][site_type]
    crawler = GenericCrawler(site_config=site_config)
    links = crawler.get_article_links(max_pages=5, max_links=50)
"""

# Core crawlers
from .base import BaseCrawler
from .generic import GenericCrawler
from .legacy import DiabetesCrawler

# Detection and configuration
from .detection import detect_site_type, load_sites_config

# Convenience functions
from .scraper import (
    quick_crawl_yhoccongdong,
    quick_crawl_who,
    quick_crawl_niddk,
    quick_crawl_all,
    get_article_links,
    run_crawler_with_custom_params,
)

# Legacy functions (deprecated)
from .scraper import run_diabetes_crawler, get_article_links_legacy

# Utilities
from .utils import configure_logging, normalize_url, create_slug_from_url

# Package version
__version__ = "2.0.0"
__author__ = "RAG Crawler Team"

# Public API
__all__ = [
    # Core crawlers
    "BaseCrawler",
    "GenericCrawler", 
    "DiabetesCrawler",
    
    # Detection and configuration
    "detect_site_type",
    "load_sites_config",
    
    # Convenience functions
    "quick_crawl_yhoccongdong",
    "quick_crawl_who",
    "quick_crawl_niddk", 
    "quick_crawl_all",
    "get_article_links",
    "run_crawler_with_custom_params",
    
    # Legacy (deprecated)
    "run_diabetes_crawler",
    "get_article_links_legacy",
    
    # Utilities
    "configure_logging",
    "normalize_url", 
    "create_slug_from_url",
]
