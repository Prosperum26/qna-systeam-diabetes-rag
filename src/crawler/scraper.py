import logging

from .impl import DiabetesCrawler, configure_logging


def run_diabetes_crawler(max_articles: int = 5, base_dir: str = "data") -> None:
    """
    Convenience entrypoint for running the Diabetes crawler from CLI or notebooks.
    """
    configure_logging(logging.INFO)
    crawler = DiabetesCrawler()
    crawler.crawl(max_articles=max_articles, base_dir=base_dir)


__all__ = ["run_diabetes_crawler"]
