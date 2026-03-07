import logging

from .impl import DiabetesCrawler, configure_logging


def run_diabetes_crawler(max_articles: int = 5, base_dir: str = "data", use_ajax: bool = True) -> None:
    """
    Convenience entrypoint for running the Diabetes crawler from CLI or notebooks.
    
    Args:
        max_articles: Maximum number of articles to crawl
        base_dir: Base directory for saving data
        use_ajax: Whether to use AJAX pagination (default: True)
    """
    configure_logging(logging.INFO)
    crawler = DiabetesCrawler()
    crawler.crawl(max_articles=max_articles, base_dir=base_dir, use_ajax=use_ajax)


__all__ = ["run_diabetes_crawler"]
