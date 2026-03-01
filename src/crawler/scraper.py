"""
Crawl nội dung từ 1 trang web.
Trả về list các document (text + metadata: url, title).
"""
from pathlib import Path
from typing import Optional

# TODO: Implement logic crawl
# - Dùng requests + BeautifulSoup hoặc Scrapy
# - Hỗ trợ crawl theo depth (link trong link)
# - Lưu raw HTML/text vào data/raw/


class WebScraper:
    """Crawl và extract text từ website."""

    def __init__(self, base_url: str, max_depth: int = 2, output_dir: Optional[Path] = None):
        self.base_url = base_url
        self.max_depth = max_depth
        self.output_dir = output_dir or Path("data/raw")

    def crawl(self) -> list[dict]:
        """
        Crawl website, trả về list dict:
        [{"content": str, "url": str, "title": str}, ...]
        """
        # TODO: Implement
        raise NotImplementedError("Implement crawl logic tại đây")

    def save_raw(self, documents: list[dict]) -> Path:
        """Lưu raw documents ra file (JSON/text) để xử lý sau."""
        # TODO: Implement
        raise NotImplementedError("Implement save logic tại đây")
