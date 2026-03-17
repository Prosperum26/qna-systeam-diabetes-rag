"""Convenience functions for easy crawling with modern architecture.

This module provides simple, user-friendly functions for common crawling tasks.
For advanced usage, use the GenericCrawler directly or crawl_runner.py.
"""

import logging
import warnings
from typing import List, Optional

# Import from new architecture
from .legacy import DiabetesCrawler
from .generic import GenericCrawler
from .detection import detect_site_type, load_sites_config
from .utils import configure_logging


def run_diabetes_crawler(max_articles: int = 5, base_dir: str = "data", use_ajax: bool = True) -> None:
    """
    Legacy convenience function for yhoccongdong.com crawling.
    
    DEPRECATED: Use quick_crawl_yhoccongdong() or crawl_runner.py instead.
    
    Args:
        max_articles: Maximum number of articles to crawl (default: 5)
        base_dir: Base directory for saving data (default: "data")
        use_ajax: Whether to use AJAX pagination (default: True)
    """
    warnings.warn(
        "run_diabetes_crawler() is deprecated. Use quick_crawl_yhoccongdong() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Input validation
    if not isinstance(max_articles, int) or max_articles < 0:
        raise ValueError("max_articles must be a non-negative integer")
    if not isinstance(base_dir, str) or not base_dir.strip():
        raise ValueError("base_dir must be a non-empty string")
    if not isinstance(use_ajax, bool):
        raise ValueError("use_ajax must be a boolean")
    
    try:
        configure_logging(logging.INFO)
        crawler = DiabetesCrawler()
        crawler.crawl(max_articles=max_articles, base_dir=base_dir, use_ajax=use_ajax)
    except Exception as exc:
        logging.error("Failed to run diabetes crawler: %s", exc)
        raise


def quick_crawl_yhoccongdong(max_articles: int = 50, output_dir: str = "data/documents") -> int:
    """
    Quick crawl yhoccongdong.com with modern architecture.
    
    Args:
        max_articles: Maximum number of articles to crawl (default: 50)
        output_dir: Directory to save documents (default: "data/documents")
        
    Returns:
        Number of successfully crawled articles
        
    Example:
        >>> count = quick_crawl_yhoccongdong(max_articles=100)
        >>> print(f"Crawled {count} articles")
    """
    try:
        from pipelines.crawl_runner import run_single_url
        
        configure_logging(logging.INFO)
        
        run_single_url(
            url="https://yhoccongdong.com/tieu-duong/",
            output_dir=output_dir,
            category="general",
            depth=2,  # Discover + process articles
            max_article=max_articles
        )
        
        logging.info(f"Quick crawl completed for yhoccongdong.com (max_articles={max_articles})")
        return max_articles
        
    except Exception as exc:
        logging.error("Failed to quick crawl yhoccongdong: %s", exc)
        raise


def quick_crawl_who(output_dir: str = "data/documents") -> int:
    """
    Quick crawl WHO diabetes fact sheet.
    
    Args:
        output_dir: Directory to save documents (default: "data/documents")
        
    Returns:
        Number of successfully crawled articles (always 1 for WHO)
        
    Example:
        >>> count = quick_crawl_who()
        >>> print(f"Crawled {count} WHO articles")
    """
    try:
        from pipelines.crawl_runner import run_single_url
        
        configure_logging(logging.INFO)
        
        run_single_url(
            url="https://www.who.int/news-room/fact-sheets/detail/diabetes",
            output_dir=output_dir,
            category="concepts",
            depth=1,  # Single page only
            max_article=1
        )
        
        logging.info("Quick crawl completed for WHO diabetes fact sheet")
        return 1
        
    except Exception as exc:
        logging.error("Failed to quick crawl WHO: %s", exc)
        raise


def quick_crawl_niddk(max_articles: int = 50, output_dir: str = "data/documents") -> int:
    """
    Quick crawl NIDDK diabetes information.
    
    Args:
        max_articles: Maximum number of articles to crawl (default: 50)
        output_dir: Directory to save documents (default: "data/documents")
        
    Returns:
        Number of successfully crawled articles
        
    Example:
        >>> count = quick_crawl_niddk(max_articles=100)
        >>> print(f"Crawled {count} NIDDK articles")
    """
    try:
        from pipelines.crawl_runner import run_single_url
        
        configure_logging(logging.INFO)
        
        run_single_url(
            url="https://www.niddk.nih.gov/health-information/diabetes",
            output_dir=output_dir,
            category="general",
            depth=2,  # Discover + process articles
            max_article=max_articles
        )
        
        logging.info(f"Quick crawl completed for NIDDK (max_articles={max_articles})")
        return max_articles
        
    except Exception as exc:
        logging.error("Failed to quick crawl NIDDK: %s", exc)
        raise


def quick_crawl_all(output_dir: str = "data/documents") -> dict:
    """
    Quick crawl all configured sites.
    
    Args:
        output_dir: Directory to save documents (default: "data/documents")
        
    Returns:
        Dictionary with crawl results per site
        
    Example:
        >>> results = quick_crawl_all()
        >>> print(f"Results: {results}")
    """
    try:
        from pipelines.crawl_runner import run_config_mode
        import json
        
        configure_logging(logging.INFO)
        
        # Load config
        with open("src/crawler/config/configURL.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Run config mode
        run_config_mode(config, output_dir)
        
        # Return summary
        results = {
            "total_urls": len(config.get('urls', [])),
            "enabled_urls": len([u for u in config.get('urls', []) if u.get('enabled', True)]),
            "output_dir": output_dir
        }
        
        logging.info(f"Quick crawl all completed: {results}")
        return results
        
    except Exception as exc:
        logging.error("Failed to quick crawl all: %s", exc)
        raise


def get_article_links(site_type: str = "yhoccongdong", max_pages: int = 10, max_links: int = 50) -> List[str]:
    """
    Get article URLs without crawling the full content using modern architecture.
    
    Args:
        site_type: Site to crawl ('yhoccongdong', 'who', 'niddk', 'diabetes_org')
        max_pages: Maximum number of pages to check (default: 10)
        max_links: Maximum number of links to collect (default: 50)
        
    Returns:
        List of unique article URLs
        
    Example:
        >>> urls = get_article_links('yhoccongdong', max_pages=5, max_links=100)
        >>> print(f"Found {len(urls)} articles")
    """
    # Input validation
    if not isinstance(max_pages, int) or max_pages < 0:
        raise ValueError("max_pages must be a non-negative integer")
    if not isinstance(max_links, int) or max_links < 0:
        raise ValueError("max_links must be a non-negative integer")
    
    try:
        configure_logging(logging.WARNING)  # Less verbose for link extraction
        
        # Load site configuration
        sites_config = load_sites_config()
        
        if site_type == "yhoccongdong":
            # Use legacy DiabetesCrawler for backward compatibility
            crawler = DiabetesCrawler()
            links = crawler.get_article_links(max_pages=max_pages, max_links=max_links, use_ajax=True)
        else:
            # Use GenericCrawler for other sites
            if site_type not in sites_config.get('sites', {}):
                raise ValueError(f"Unknown site type: {site_type}")
            
            site_config = sites_config['sites'][site_type]
            crawler = GenericCrawler(site_config=site_config)
            links = crawler.get_article_links(max_pages=max_pages, max_links=max_links)
        
        return [link.url for link in links]
        
    except Exception as exc:
        logging.error("Failed to get article links: %s", exc)
        raise


def run_crawler_with_custom_params(
    site_type: str = "yhoccongdong",
    max_articles: int = 50,
    max_pages: int = 100,
    delay_seconds: float = 2.0,
    output_dir: str = "data/documents"
) -> int:
    """
    Run crawler with custom parameters for fine-tuned control using modern architecture.
    
    Args:
        site_type: Site to crawl ('yhoccongdong', 'who', 'niddk', 'diabetes_org')
        max_articles: Maximum articles to crawl
        max_pages: Maximum pages to scan for links
        delay_seconds: Delay between requests (default: 2.0)
        output_dir: Directory to save data
        
    Returns:
        Number of successfully crawled articles
        
    Example:
        >>> count = run_crawler_with_custom_params(
        ...     site_type='yhoccongdong',
        ...     max_articles=100,
        ...     delay_seconds=1.5
        ... )
        >>> print(f"Crawled {count} articles")
    """
    # Input validation
    if not isinstance(max_articles, int) or max_articles < 0:
        raise ValueError("max_articles must be a non-negative integer")
    if not isinstance(max_pages, int) or max_pages < 0:
        raise ValueError("max_pages must be a non-negative integer")
    if not isinstance(delay_seconds, (int, float)) or delay_seconds < 0:
        raise ValueError("delay_seconds must be a non-negative number")
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ValueError("output_dir must be a non-empty string")
    
    try:
        configure_logging(logging.INFO)
        
        # Use modern architecture through crawl_runner
        from pipelines.crawl_runner import run_single_url
        
        # Determine URL based on site type
        site_urls = {
            "yhoccongdong": "https://yhoccongdong.com/tieu-duong/",
            "who": "https://www.who.int/news-room/fact-sheets/detail/diabetes",
            "niddk": "https://www.niddk.nih.gov/health-information/diabetes",
            "diabetes_org": "https://diabetes.org/"
        }
        
        if site_type not in site_urls:
            raise ValueError(f"Unknown site type: {site_type}")
        
        # Determine depth based on site type
        depth = 2 if site_type in ["yhoccongdong", "niddk"] else 1
        
        run_single_url(
            url=site_urls[site_type],
            output_dir=output_dir,
            category="general",
            depth=depth,
            max_article=max_articles
        )
        
        logging.info(f"Custom crawl completed for {site_type} (max_articles={max_articles})")
        return max_articles
        
    except Exception as exc:
        logging.error("Failed to run crawler with custom params: %s", exc)
        raise


# Legacy functions with deprecation warnings
def get_article_links_legacy(max_pages: int = 100, max_links: int = 200, use_ajax: bool = True) -> List[str]:
    """
    Legacy function - use get_article_links() instead.
    """
    warnings.warn(
        "get_article_links_legacy() is deprecated. Use get_article_links('yhoccongdong', ...) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_article_links("yhoccongdong", max_pages, max_links)


# Export public API
__all__ = [
    # Modern convenience functions
    "quick_crawl_yhoccongdong",
    "quick_crawl_who", 
    "quick_crawl_niddk",
    "quick_crawl_all",
    "get_article_links",
    "run_crawler_with_custom_params",
    
    # Legacy functions (deprecated)
    "run_diabetes_crawler",
    "get_article_links_legacy",
]
