"""Module crawl dữ liệu từ web (dự án Tiểu đường)."""

from .scraper import run_diabetes_crawler
from .impl import DiabetesCrawler

__all__ = ["run_diabetes_crawler", "DiabetesCrawler"]
