import logging
from typing import List

from .impl import DiabetesCrawler, configure_logging


def run_diabetes_crawler(max_articles: int = 5, base_dir: str = "data", use_ajax: bool = True) -> None:
    """
    Convenience entrypoint for running the Diabetes crawler from CLI or notebooks.
    
    Args:
        max_articles: Maximum number of articles to crawl (default: 5)
        base_dir: Base directory for saving data (default: "data")
        use_ajax: Whether to use AJAX pagination (default: True)
    
    Example:
        >>> run_diabetes_crawler(max_articles=50, use_ajax=True)
        >>> run_diabetes_crawler(max_articles=100, use_ajax=False)
    """
    configure_logging(logging.INFO)
    crawler = DiabetesCrawler()
    crawler.crawl(max_articles=max_articles, base_dir=base_dir, use_ajax=use_ajax)


def get_article_links(max_pages: int = 100, max_links: int = 200, use_ajax: bool = True) -> List[str]:
    """
    Get article URLs without crawling the full content.
    
    Args:
        max_pages: Maximum number of pages to check (default: 100)
        max_links: Maximum number of links to collect (default: 200)
        use_ajax: Whether to use AJAX pagination (default: True)
    
    Returns:
        List of unique article URLs
        
    Example:
        >>> urls = get_article_links(max_pages=50, max_links=100)
        >>> print(f"Found {len(urls)} articles")
    """
    configure_logging(logging.WARNING)  # Less verbose for link extraction
    crawler = DiabetesCrawler()
    links = crawler.get_article_links(max_pages=max_pages, max_links=max_links, use_ajax=use_ajax)
    return [link.url for link in links]


def run_crawler_with_custom_params(
    max_articles: int = 50,
    max_pages: int = 100,
    delay_seconds: float = 2.0,
    base_dir: str = "data",
    use_ajax: bool = True
) -> None:
    """
    Run crawler with custom parameters for fine-tuned control.
    
    Args:
        max_articles: Maximum articles to crawl
        max_pages: Maximum pages to scan for links
        delay_seconds: Delay between requests (default: 2.0)
        base_dir: Directory to save data
        use_ajax: Use AJAX pagination
        
    Example:
        >>> run_crawler_with_custom_params(
        ...     max_articles=100,
        ...     max_pages=200,
        ...     delay_seconds=1.5,
        ...     use_ajax=True
        ... )
    """
    configure_logging(logging.INFO)
    crawler = DiabetesCrawler(delay_seconds=delay_seconds)
    
    # First get links
    links = crawler.get_article_links(max_pages=max_pages, max_links=max_articles, use_ajax=use_ajax)
    print(f"Discovered {len(links)} article links")
    
    # Then crawl
    crawler.crawl(max_articles=max_articles, base_dir=base_dir, use_ajax=use_ajax)


__all__ = ["run_diabetes_crawler", "get_article_links", "run_crawler_with_custom_params"]
