import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import md5
from typing import Dict, Iterable, List, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag

from src.processors import clean_article_soup, normalize_text, split_sections


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0 Safari/537.36"
)


@dataclass
class ArticleLink:
    title: str
    url: str
    category: str


class BaseCrawler:
    def __init__(
        self,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        self.session.headers.update({"User-Agent": USER_AGENT})

    def fetch(self, url: str) -> Optional[str]:
        for attempt in range(1, self.max_retries + 1):
            # Delay before each request
            time.sleep(self.delay_seconds)

            try:
                self.logger.info("Fetching URL (attempt %s/%s): %s", attempt, self.max_retries, url)
                resp = self.session.get(url, timeout=self.timeout_seconds)

                if 500 <= resp.status_code < 600 or resp.status_code == 429:
                    self.logger.warning(
                        "Server error %s for %s (attempt %s)", resp.status_code, url, attempt
                    )
                    if attempt == self.max_retries:
                        return None
                    continue

                if 400 <= resp.status_code < 500:
                    self.logger.error("Client error %s for %s, skipping", resp.status_code, url)
                    return None

                resp.encoding = resp.apparent_encoding
                return resp.text
            except (requests.Timeout, requests.ConnectionError) as exc:
                self.logger.warning("Transient error for %s: %s (attempt %s)", url, exc, attempt)
                if attempt == self.max_retries:
                    self.logger.error("Giving up on %s after %s attempts", url, attempt)
                    return None
            except requests.RequestException as exc:
                self.logger.exception("Non-retryable error while fetching %s: %s", url, exc)
                return None

        return None

    def save_raw_html(self, slug: str, html: str, base_dir: str = "data") -> str:
        raw_dir = os.path.join(base_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        path = os.path.join(raw_dir, f"{slug}.html")

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        self.logger.info("Saved raw HTML to %s", path)
        return path

    def save_document(self, slug: str, document: Dict, base_dir: str = "data") -> str:
        doc_dir = os.path.join(base_dir, "documents")
        os.makedirs(doc_dir, exist_ok=True)
        path = os.path.join(doc_dir, f"{slug}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(document, f, ensure_ascii=False, indent=2)

        self.logger.info("Saved document JSON to %s", path)
        return path

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)

        query_pairs = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if not k.lower().startswith("utm_")
        ]
        new_query = urlencode(query_pairs, doseq=True)

        normalized = parsed._replace(query=new_query, fragment="")

        scheme = normalized.scheme.lower()
        netloc = normalized.netloc.lower()
        path = normalized.path.lower()

        if path != "/":
            path = path.rstrip("/")

        normalized = normalized._replace(scheme=scheme, netloc=netloc, path=path)
        final = urlunparse(normalized)

        if final.endswith("/") and final != "/":
            final = final.rstrip("/")

        return final


class DiabetesCrawler(BaseCrawler):
    BASE_CATEGORY_URL = "https://yhoccongdong.com/tieu-duong/"
    CATEGORY_SLUG = "tieu-duong"

    def __init__(
        self,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(
            delay_seconds=delay_seconds,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            session=session,
            logger=logger,
        )

        self._seen_urls: Set[str] = set()
        self._seen_hashes: Set[str] = set()
        self._seen_titles: Set[str] = set()

    def get_article_links(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """
        Discover article links from the category and pagination pages.

        If max_links được truyền vào, sẽ dừng sớm khi đã thu thập đủ số lượng link cần thiết.
        """
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

            candidates: Iterable[Tag] = soup.select("a.col-12.post-item_content-title")

            if not candidates:
                candidates = soup.select("div.post-item_content a")

            page_links_before = len(links)

            for a_tag in candidates:
                if not isinstance(a_tag, Tag):
                    continue

                href = a_tag.get("href")
                if not href:
                    continue

                if not a_tag.find("h4"):
                    continue

                if not href.startswith("https://yhoccongdong.com/"):
                    continue
                if "/tieu-duong/" not in href:
                    continue
                if "/page/" in href or "#" in href or href.lower().startswith("javascript:"):
                    continue

                title = a_tag.get_text(strip=True)
                if not title:
                    continue

                links.append(ArticleLink(title=title, url=href, category=self.CATEGORY_SLUG))

                # Dừng sớm nếu đã đủ số link yêu cầu
                if max_links is not None and len(links) >= max_links:
                    self.logger.info(
                        "Reached requested max_links=%s at page %s", max_links, page_index
                    )
                    return links

            if len(links) == page_links_before:
                self.logger.info("No new article links found on %s, stopping.", page_url)
                break

            self.logger.info(
                "Discovered %s total article links after page %s", len(links), page_index
            )
            page_index += 1

        return links

    def _extract_title(self, soup: BeautifulSoup) -> str:
        h1 = soup.select_one("div.format-post_content-object h1") or soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
            if title:
                return normalize_text(title)

        if soup.title and soup.title.string:
            return normalize_text(soup.title.string)

        return ""

    def parse(self, url: str, html: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, "html.parser")

        clean_article_soup(soup)

        title = self._extract_title(soup)
        if not title:
            self.logger.warning("Could not extract title for %s, skipping.", url)
            return None

        main_container = (
            soup.select_one("div.post-dt-content")
            or soup.select_one("div.post-content")
            or soup.find("article")
            or soup.body
        )
        if not main_container:
            self.logger.warning("No content container found for %s, skipping.", url)
            return None

        sections = split_sections(main_container)
        if not sections:
            self.logger.warning("No sections extracted for %s, skipping.", url)
            return None

        text_for_hash = "\n\n".join(section["content"] for section in sections if section.get("content"))
        normalized_text = normalize_text(text_for_hash)
        content_hash = md5(normalized_text.encode("utf-8")).hexdigest()

        normalized_url = self.normalize_url(url)
        slug = normalized_url.rstrip("/").split("/")[-1] or "index"

        crawl_time = datetime.now(timezone.utc).isoformat()

        document = {
            "doc_id": slug,
            "url": normalized_url,
            "title": title,
            "category": self.CATEGORY_SLUG,
            "sections": sections,
            "metadata": {
                "crawl_time": crawl_time,
                "hash": content_hash,
            },
        }

        return document

    def _is_duplicate(self, url: str, document: Dict) -> bool:
        normalized_url = self.normalize_url(url)
        title = normalize_text(document.get("title", ""))
        content_hash = document.get("metadata", {}).get("hash", "")

        if normalized_url in self._seen_urls:
            self.logger.info("Duplicate URL (already seen): %s", normalized_url)
            return True

        if content_hash and content_hash in self._seen_hashes:
            self.logger.info("Duplicate content hash for URL %s", normalized_url)
            return True

        if title and title in self._seen_titles:
            self.logger.info("Duplicate title for URL %s", normalized_url)
            return True

        self._seen_urls.add(normalized_url)
        if content_hash:
            self._seen_hashes.add(content_hash)
        if title:
            self._seen_titles.add(title)

        return False

    def crawl(self, max_articles: int = 5, base_dir: str = "data") -> None:
        self.logger.info("Starting crawl for category %s (max_articles=%s)", self.CATEGORY_SLUG, max_articles)

        # Chỉ discover tối đa số link cần thiết để tránh đi hết toàn bộ pagination.
        links = self.get_article_links(max_links=max_articles)
        if not links:
            self.logger.warning("No article links discovered, aborting crawl.")
            return

        processed = 0
        for article in links:
            if processed >= max_articles:
                break

            normalized_url = self.normalize_url(article.url)
            if normalized_url in self._seen_urls:
                self.logger.info("Skipping already-seen URL from discovery: %s", normalized_url)
                continue

            html = self.fetch(article.url)
            if not html:
                self.logger.error("Failed to fetch article URL: %s", article.url)
                continue

            document = self.parse(article.url, html)
            if not document:
                self.logger.error("Failed to parse article URL: %s", article.url)
                continue

            if self._is_duplicate(article.url, document):
                continue

            slug = document.get("doc_id") or normalized_url.rstrip("/").split("/")[-1] or "index"

            try:
                self.save_raw_html(slug, html, base_dir=base_dir)
                self.save_document(slug, document, base_dir=base_dir)
                self.logger.info("Successfully processed article %s (%s)", slug, normalized_url)
                processed += 1
            except OSError as exc:
                self.logger.exception("Failed to save data for %s: %s", article.url, exc)

        self.logger.info("Crawl finished. Articles processed: %s", processed)


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


__all__ = [
    "BaseCrawler",
    "DiabetesCrawler",
    "ArticleLink",
    "configure_logging",
]

