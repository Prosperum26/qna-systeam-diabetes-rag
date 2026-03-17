"""Backward compatibility exports for the crawler package.

This file provides the same interface as the old impl.py for backward compatibility.
"""

# Core components
from .base import BaseCrawler
from .generic import GenericCrawler
from .legacy import DiabetesCrawler

# Utilities
from .utils import configure_logging, normalize_url, create_slug_from_url

# Components
from .components import LinkExtractor, ArticleLink

# Pagination
from .pagination import PaginationFactory, TraditionalPagination, AjaxPagination

# Backward compatibility - expose main classes
__all__ = [
    "BaseCrawler",
    "GenericCrawler", 
    "DiabetesCrawler",
    "configure_logging",
    "normalize_url",
    "create_slug_from_url",
    "LinkExtractor",
    "ArticleLink",
    "PaginationFactory",
]
