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
import brotli

from src.processors import clean_article_soup, normalize_text, split_sections


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
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

    def _truncate_links(self, links: List[ArticleLink], max_links: Optional[int]) -> List[ArticleLink]:
        """Truncate links list to max_links if specified."""
        if max_links is not None and len(links) > max_links:
            return links[:max_links]
        return links

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
            
        Note:
            If use_ajax is True, will use AJAX pagination instead of traditional pagination.
            If max_links is provided, will stop early when enough links are collected.
        """
        links: List[ArticleLink] = []
        
        if use_ajax:
            return self._get_article_links_ajax(max_pages, max_links)
        else:
            return self._get_article_links_traditional(max_pages, max_links)
    
    def _get_article_links_traditional(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """
        Traditional pagination method (original implementation).
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
    
    def _get_article_links_ajax(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """
        AJAX pagination method for WordPress sites with load more functionality.
        Starts from page 2 since page 1 is the initial page load.
        """
        links: List[ArticleLink] = []
        seen_urls: Set[str] = set()  # Track URLs for O(1) duplicate detection
        page_index = 2  # Start from page 2 for AJAX requests
        
        # First, get the initial page to extract the nonce
        initial_html = self.fetch(self.BASE_CATEGORY_URL)
        if not initial_html:
            self.logger.error("Failed to fetch initial page, cannot extract nonce.")
            return links
            
        # Extract nonce from the initial page
        nonce = self._extract_ajax_nonce(initial_html)
        if not nonce:
            self.logger.error("Could not extract AJAX nonce from initial page.")
            return links
        
        # Parse initial page for articles
        soup = BeautifulSoup(initial_html, "html.parser")
        initial_links = self._parse_articles_from_soup(soup)
        for link in initial_links:
            if link.url not in seen_urls:
                links.append(link)
                seen_urls.add(link.url)
        
        self.logger.info("Found %s articles on initial page", len(initial_links))
        
        # Apply max_links limit consistently
        links = self._truncate_links(links, max_links)
        if max_links is not None and len(links) >= max_links:
            return links
        
        # Continue with AJAX pagination starting from page 2
        while True:
            if max_pages is not None and (page_index - 1) > max_pages:  # -1 because we start from page 2
                break
                
            # Check if we've reached the limit
            if max_links is not None and len(links) >= max_links:
                break
                
            # Fetch next page via AJAX
            ajax_html = self._fetch_ajax_page(page_index, nonce)
            if not ajax_html:
                self.logger.info("No more articles via AJAX at page %s, stopping.", page_index)
                break
            
            # Parse AJAX response
            ajax_soup = BeautifulSoup(ajax_html, "html.parser")
            ajax_links = self._parse_articles_from_soup(ajax_soup)
            
            if not ajax_links:
                self.logger.info("No new articles found in AJAX response at page %s, stopping.", page_index)
                break
            
            # Add new links
            page_links_before = len(links)
            for link in ajax_links:
                # Check for duplicates using O(1) set lookup
                if link.url not in seen_urls:
                    links.append(link)
                    seen_urls.add(link.url)
                    
                    # Stop early if we've reached the limit
                    if max_links is not None and len(links) >= max_links:
                        self.logger.info(
                            "Reached requested max_links=%s at AJAX page %s", max_links, page_index
                        )
                        return self._truncate_links(links, max_links)
            
            if len(links) == page_links_before:
                self.logger.info("No new unique articles found in AJAX response at page %s, stopping.", page_index)
                break
            
            self.logger.info(
                "Discovered %s total article links after AJAX page %s (%d new this page)", 
                len(links), page_index, len(ajax_links)
            )
            page_index += 1  # Increment to next page
        
        return self._truncate_links(links, max_links)
    
    def _extract_ajax_nonce(self, html: str) -> Optional[str]:
        """Extract AJAX nonce from the page HTML."""
        try:
            # Look for nonce in JavaScript variables
            import re
            
            # Pattern to match nonce in JavaScript
            patterns = [
                r'nonce["\']?\s*:\s*["\']([a-f0-9]+)["\']',
                r'_ajax_nonce["\']?\s*:\s*["\']([a-f0-9]+)["\']',
                r'nonce_ajax["\']?\s*=\s*{[^}]*nonce["\']?\s*:\s*["\']([a-f0-9]+)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    nonce = match.group(1)
                    self.logger.info("Found AJAX nonce: %s", nonce)
                    return nonce
            
            # If not found in JS, try to find in meta tags or other locations
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for nonce in data attributes
            nonce_elem = soup.find(attrs={"data-nonce": True})
            if nonce_elem:
                nonce = nonce_elem.get("data-nonce")
                if nonce:
                    self.logger.info("Found AJAX nonce in data attribute: %s", nonce)
                    return nonce
            
            self.logger.warning("Could not find AJAX nonce in page HTML")
            return None
            
        except Exception as exc:
            self.logger.exception("Error extracting AJAX nonce: %s", exc)
            return None
    
    def _fetch_ajax_page(self, page: int, nonce: str) -> Optional[str]:
        """Fetch articles via AJAX request."""
        ajax_url = f"{self.BASE_CATEGORY_URL}wp-admin/admin-ajax.php"
        
        payload = {
            "action": "watch_more_ar",
            "page": str(page),
            "view": "cancer-default",
            "_ajax_nonce": nonce,
        }
        
        try:
            self.logger.info("Fetching AJAX page %s with payload: %s", page, payload)
            self.logger.info("AJAX URL: %s", ajax_url)
            
            # Update session headers for AJAX - match browser exactly
            original_headers = self.session.headers.copy()
            try:
                self.session.headers.update({
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
                    "Referer": self.BASE_CATEGORY_URL,
                    "Origin": "https://yhoccongdong.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                })
                
                # Use POST request for AJAX
                time.sleep(self.delay_seconds)  # Respect delay
                
                resp = self.session.post(
                    ajax_url, 
                    data=payload, 
                    timeout=self.timeout_seconds
                )
                
                self.logger.info("AJAX POST response status: %s", resp.status_code)
                
                # If POST fails, try GET
                if resp.status_code != 200:
                    self.logger.warning("POST failed, trying GET method...")
                    get_params = payload.copy()
                    resp = self.session.get(
                        ajax_url, 
                        params=get_params, 
                        timeout=self.timeout_seconds
                    )
                    self.logger.info("AJAX GET response status: %s", resp.status_code)
            finally:
                # Always restore original headers
                self.session.headers = original_headers
            
            self.logger.info("AJAX response headers: %s", dict(resp.headers))
            
            if resp.status_code == 200:
                # Handle Brotli compression
                response_text = resp.text
                content_encoding = resp.headers.get('content-encoding', '').lower()
                
                if content_encoding == 'br':
                    try:
                        # Decompress Brotli content
                        response_text = brotli.decompress(resp.content).decode('utf-8')
                        self.logger.info("Successfully decompressed Brotli response")
                    except Exception as e:
                        self.logger.error("Failed to decompress Brotli: %s", e)
                        # Try to decode as raw content first
                        try:
                            response_text = resp.content.decode('utf-8')
                            self.logger.info("Successfully decoded raw content as UTF-8")
                        except UnicodeDecodeError:
                            # Last resort: use resp.text (may be garbage but won't crash)
                            response_text = resp.text
                            self.logger.warning("Using resp.text as last resort for Brotli failure")
                
                self.logger.info("AJAX response content type: %s", resp.headers.get('content-type', 'unknown'))
                self.logger.info("AJAX response encoding: %s", content_encoding)
                self.logger.info("AJAX response length: %d chars", len(response_text))
                self.logger.debug("AJAX response content (first 1000 chars): %s", response_text[:1000])
                
                # The response should be HTML content, not JSON
                if response_text.strip():
                    # Check if it's HTML with article content
                    if '<article' in response_text or 'post-item' in response_text or 'class="post' in response_text:
                        self.logger.info("Got HTML response with article content")
                        return response_text
                    else:
                        self.logger.warning("Response doesn't contain expected article HTML")
                        self.logger.info("Full AJAX response for debugging:")
                        self.logger.info("=" * 50)
                        self.logger.info(response_text)
                        self.logger.info("=" * 50)
                        return response_text
                else:
                    self.logger.warning("Got empty response from AJAX")
                    return None
            else:
                self.logger.warning("AJAX request failed with status %s", resp.status_code)
                # Try to get error details
                try:
                    error_text = resp.text[:500]  # First 500 chars
                    self.logger.warning("Error response: %s", error_text)
                except:
                    pass
                return None
                
        except Exception as exc:
            self.logger.exception("Error fetching AJAX page %s: %s", page, exc)
            return None
    
    def _parse_articles_from_soup(self, soup: BeautifulSoup) -> List[ArticleLink]:
        """Parse article links from BeautifulSoup object."""
        links: List[ArticleLink] = []
        
        # Look for article containers
        candidates: Iterable[Tag] = soup.select("a.col-12.post-item_content-title")
        
        if not candidates:
            candidates = soup.select("div.post-item_content a")
        
        if not candidates:
            candidates = soup.select(".post-item a")
        
        for a_tag in candidates:
            if not isinstance(a_tag, Tag):
                continue
                
            href = a_tag.get("href")
            if not href:
                continue
                
            # Validate URL
            if not href.startswith("https://yhoccongdong.com/"):
                continue
            if "/tieu-duong/" not in href:
                continue
            if "/page/" in href or "#" in href or href.lower().startswith("javascript:"):
                continue
            
            # Extract title
            title = a_tag.get_text(strip=True)
            if not title:
                # Try to find title in h4 within the link
                h4 = a_tag.find("h4")
                if h4:
                    title = h4.get_text(strip=True)
                else:
                    continue
            
            links.append(ArticleLink(title=title, url=href, category=self.CATEGORY_SLUG))
        
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

    def crawl(self, max_articles: int = 5, base_dir: str = "data", use_ajax: bool = True) -> None:
        self.logger.info("Starting crawl for category %s (max_articles=%s, use_ajax=%s)", self.CATEGORY_SLUG, max_articles, use_ajax)

        # Chỉ discover tối đa số link cần thiết để tránh đi hết toàn bộ pagination.
        links = self.get_article_links(max_links=max_articles, use_ajax=use_ajax)
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

