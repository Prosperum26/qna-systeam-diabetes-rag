"""Legacy DiabetesCrawler for backward compatibility."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

from bs4 import BeautifulSoup, Tag

from ..base import BaseCrawler
from ..utils import normalize_url


class ArticleLink:
    """Represents a discovered article link (legacy compatibility)."""
    
    def __init__(self, title: str, url: str, category: str = "general"):
        self.title = title
        self.url = url
        self.category = category


class DiabetesCrawler(BaseCrawler):
    """
    Legacy specialized crawler for yhoccongdong.com.
    
    Maintained for backward compatibility with existing code.
    """
    
    BASE_CATEGORY_URL = "https://yhoccongdong.com/tieu-duong/"
    CATEGORY_SLUG = "tieu-duong"

    def __init__(
        self,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> None:
        """Initialize DiabetesCrawler with legacy parameters."""
        super().__init__(
            delay_seconds=delay_seconds,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            session=session,
            logger=logger,
        )
        
        self._seen_urls: set[str] = set()
        self._seen_hashes: set[str] = set()
        self._seen_titles: set[str] = set()

    def get_article_links(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
        use_ajax: bool = True,
    ) -> List[ArticleLink]:
        """
        Discover article links from the category and pagination pages.
        
        Args:
            max_pages: Maximum number of pages to crawl (None for unlimited)
            max_links: Maximum number of links to collect (None for unlimited)
            use_ajax: Whether to use AJAX pagination (default: True)
        
        Returns:
            List of unique ArticleLink objects
        """
        if use_ajax:
            return self._get_article_links_ajax(max_pages, max_links)
        else:
            return self._get_article_links_traditional(max_pages, max_links)
    
    def _get_article_links_traditional(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """Traditional pagination method (original implementation)."""
        links: List[ArticleLink] = []
        page_index = 1

        while True:
            if page_index == 1:
                page_url = self.BASE_CATEGORY_URL
            else:
                page_url = f"{self.BASE_CATEGORY_URL}page/{page_index}/"

            if max_pages is not None and page_index > max_pages:
                break

            html = self.fetch(page_url)
            if not html:
                self.logger.warning("No HTML returned for category page %s, stopping pagination.", page_url)
                break

            soup = BeautifulSoup(html, "html.parser")

            candidates: list[Tag] = soup.select("a.col-12.post-item_content-title")

            if not candidates:
                candidates = soup.select("div.post-item_content a")

            page_links_before = len(links)

            for a_tag in candidates:
                if not isinstance(a_tag, Tag):
                    continue

                href = a_tag.get("href")
                if not href:
                    continue

                full_url = self.normalize_url(href)
                if full_url in self._seen_urls:
                    continue

                title = self._extract_title(a_tag)
                if not title or title in self._seen_titles:
                    continue

                article_link = ArticleLink(title=title, url=full_url, category="general")
                links.append(article_link)
                self._seen_urls.add(full_url)
                self._seen_titles.add(title)

            if len(links) == page_links_before:
                self.logger.info("No new links found on page %s, stopping pagination.", page_url)
                break

            self.logger.info("Found %d links on page %s (total: %d)", 
                          len(links) - page_links_before, page_url, len(links))

            page_index += 1

        return self._truncate_links(links, max_links)
    
    def _get_article_links_ajax(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """AJAX pagination method (original implementation)."""
        links: List[ArticleLink] = []
        page_index = 1

        while True:
            if page_index == 1:
                page_url = self.BASE_CATEGORY_URL
            else:
                page_url = f"{self.BASE_CATEGORY_URL}?page={page_index}"

            if max_pages is not None and page_index > max_pages:
                break

            html = self.fetch(page_url)
            if not html:
                self.logger.warning("No HTML returned for AJAX page %s, stopping pagination.", page_url)
                break

            soup = BeautifulSoup(html, "html.parser")

            candidates: list[Tag] = soup.select("a.col-12.post-item_content-title")

            if not candidates:
                candidates = soup.select("div.post-item_content a")

            page_links_before = len(links)

            for a_tag in candidates:
                if not isinstance(a_tag, Tag):
                    continue

                href = a_tag.get("href")
                if not href:
                    continue

                full_url = self.normalize_url(href)
                if full_url in self._seen_urls:
                    continue

                title = self._extract_title(a_tag)
                if not title or title in self._seen_titles:
                    continue

                article_link = ArticleLink(title=title, url=full_url, category="general")
                links.append(article_link)
                self._seen_urls.add(full_url)
                self._seen_titles.add(title)

            if len(links) == page_links_before:
                self.logger.info("No new links found via AJAX page %s, stopping pagination.", page_url)
                break

            self.logger.info("Found %d links via AJAX page %s (total: %d)", 
                          len(links) - page_links_before, page_url, len(links))

            page_index += 1

        return self._truncate_links(links, max_links)

    def normalize_url(self, url: str) -> str:
        """Normalize URL for yhoccongdong.com."""
        return normalize_url(url, self.BASE_CATEGORY_URL)

    def _extract_title(self, element: Tag) -> str:
        """Extract and normalize title from element."""
        try:
            from processors import normalize_text
            return normalize_text(element.get_text())
        except Exception:
            return element.get_text().strip()

    def _truncate_links(self, links: List[ArticleLink], max_links: Optional[int]) -> List[ArticleLink]:
        """Truncate links list to max_links if specified."""
        if max_links is not None and len(links) > max_links:
            return links[:max_links]
        return links

    def crawl(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = 50,
        base_dir: str = "data/documents"
    ) -> int:
        """
        Crawl category page and process discovered articles.
        
        Args:
            max_pages: Maximum pages to discover
            max_links: Maximum articles to process
            base_dir: Base directory for saving documents
            
        Returns:
            Number of successfully processed articles
        """
        self.logger.info(f"Starting legacy crawl (max_pages={max_pages}, max_links={max_links})")
        
        # Discover article links
        article_links = self.get_article_links(max_pages=max_pages, max_links=max_links, use_ajax=True)
        
        if not article_links:
            self.logger.warning("No article links discovered")
            return 0
        
        # Process each article
        processed = 0
        
        for article in article_links:
            try:
                html = self.fetch(article.url)
                if not html:
                    continue

                document = self.parse(article.url, html)
                if not document:
                    continue

                if self._is_duplicate(article.url, document):
                    continue

                slug = document.get("doc_id") or article.url.rstrip("/").split("/")[-1] or "index"

                self.save_raw_html(slug, html, base_dir=base_dir)
                self.save_document(slug, document, base_dir=base_dir)
                self.logger.info("Successfully processed article %s (%s)", slug, article.url)
                processed += 1

            except Exception as e:
                self.logger.exception("Error processing article %s: %s", article.url, e)

        self.logger.info("Legacy crawl finished. Articles processed: %s", processed)
        return processed

    def parse(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse article HTML into structured document."""
        try:
            from processors import clean_article_soup, split_sections, normalize_text
            
            soup = BeautifulSoup(html, "html.parser")
            clean_article_soup(soup)
            sections = split_sections(soup.body if soup.body else soup)

            if not sections:
                return None

            title = ""
            title_elem = soup.find("h1")
            if title_elem:
                title = normalize_text(title_elem.get_text())
            elif soup.title:
                title = normalize_text(soup.title.string)

            if not title:
                title = url

            return {
                "doc_id": self._create_doc_id(url),
                "url": self.normalize_url(url),
                "title": title,
                "category": "general",
                "sections": sections,
                "metadata": {
                    "crawl_time": datetime.now(timezone.utc).isoformat(),
                    "source_url": url,
                    "crawler_type": "DiabetesCrawler"
                }
            }

        except Exception as e:
            self.logger.exception("Failed to parse %s: %s", url, e)
            return None

    def _create_doc_id(self, url: str) -> str:
        """Create document ID from URL."""
        try:
            from ..utils import create_slug_from_url
            return create_slug_from_url(url)
        except Exception:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").replace(".", "_")
            path = parsed.path.strip("/").replace("/", "_")
            return f"{domain}_{path}" or "unknown"

    def _is_duplicate(self, url: str, document: Dict[str, Any]) -> bool:
        """Check if document is duplicate."""
        try:
            import hashlib
            
            content_hash = hashlib.md5(
                json.dumps(document["sections"], sort_keys=True).encode()
            ).hexdigest()
            
            if content_hash in self._seen_hashes:
                self.logger.info("Skipping duplicate content: %s", url)
                return True
            
            self._seen_hashes.add(content_hash)
            return False
            
        except Exception:
            return False
