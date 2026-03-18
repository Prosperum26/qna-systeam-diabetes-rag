"""Pagination strategies for different website types."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ..components.links import LinkExtractor, ArticleLink
from ..base import BaseCrawler


class PaginationStrategy(ABC):
    """Abstract base class for pagination strategies."""
    
    @abstractmethod
    def get_links(
        self, 
        crawler: BaseCrawler,
        link_extractor: LinkExtractor,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None
    ) -> List[ArticleLink]:
        """
        Get article links using this pagination strategy.
        
        Args:
            crawler: Crawler instance
            link_extractor: Link extractor instance
            max_pages: Maximum pages to crawl
            max_links: Maximum links to collect
            
        Returns:
            List of article links
        """
        pass


class TraditionalPagination(PaginationStrategy):
    """Traditional URL-based pagination (e.g., /page/2/, /page/3/)."""
    
    def get_links(
        self, 
        crawler: BaseCrawler,
        link_extractor: LinkExtractor,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None
    ) -> List[ArticleLink]:
        """Get links using traditional pagination."""
        links: List[ArticleLink] = []
        site_config = link_extractor.site_config
        pagination_config = site_config.get('pagination', {})
        
        page_index = 1
        base_url = site_config.get('base_url', '')
        url_pattern = pagination_config.get('url_pattern', '{base_url}')
        
        while True:
            # Build page URL
            if page_index == 1:
                page_url = base_url
            else:
                page_url = url_pattern.format(
                    base_url=base_url.rstrip('/'),
                    page=page_index
                )
            
            if max_pages is not None and page_index > max_pages:
                break
            
            # Fetch page
            html = crawler.fetch(page_url)
            if not html:
                crawler.logger.warning("No HTML returned for page %s, stopping pagination.", page_url)
                break
            
            # Extract links
            soup = BeautifulSoup(html, "html.parser")
            page_links = link_extractor.extract_links_from_page(soup)
            
            # Check if we found new links
            if not page_links:
                crawler.logger.info("No new links found on page %s, stopping pagination.", page_url)
                break
            
            links.extend(page_links)
            crawler.logger.info("Found %d links on page %s (total: %d)", 
                              len(page_links), page_url, len(links))
            
            # Stop if max_links reached
            if max_links is not None and len(links) >= max_links:
                break
            
            page_index += 1
        
        return link_extractor.truncate_links(links, max_links)


class AjaxPagination(PaginationStrategy):
    """AJAX-based pagination (e.g., "Load More" buttons)."""
    
    def get_links(
        self, 
        crawler: BaseCrawler,
        link_extractor: LinkExtractor,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None
    ) -> List[ArticleLink]:
        """Get links using AJAX pagination with robust implementation."""
        links: List[ArticleLink] = []
        site_config = link_extractor.site_config
        ajax_config = site_config.get('pagination', {}).get('ajax', {})
        
        if not ajax_config:
            crawler.logger.warning("AJAX configuration not found, falling back to traditional pagination")
            # Fallback to traditional pagination
            traditional = TraditionalPagination()
            return traditional.get_links(crawler, link_extractor, max_pages, max_links)
        
        # Get configuration from sites_config
        base_url = site_config.get('base_url', '')
        ajax_url = ajax_config.get('ajax_url', f"{base_url}wp-admin/admin-ajax.php")
        action = ajax_config.get('action', 'watch_more_ar')
        view = ajax_config.get('view', 'cancer-default')
        nonce_param = ajax_config.get('nonce_param', '_ajax_nonce')
        initial_page = ajax_config.get('initial_page', 1)
        
        # Track URLs for O(1) duplicate detection
        seen_urls: set[str] = set()
        page_index = 2  # Start from page 2 for AJAX requests
        
        # Step 1: Get the initial page to extract nonce and initial articles
        crawler.logger.info("Fetching initial page to extract nonce and initial articles")
        initial_html = crawler.fetch(base_url)
        if not initial_html:
            crawler.logger.error("Failed to fetch initial page, cannot extract nonce.")
            return links
            
        # Extract nonce from the initial page
        nonce = self._extract_ajax_nonce(initial_html, nonce_param, crawler, ajax_config)
        if not nonce:
            crawler.logger.error("Could not extract AJAX nonce from initial page.")
            return links
        
        # Parse initial page for articles
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(initial_html, "html.parser")
        initial_links = self._parse_articles_from_soup(soup, link_extractor, site_config)
        
        for link in initial_links:
            if link.url not in seen_urls:
                links.append(link)
                seen_urls.add(link.url)
        
        crawler.logger.info("Found %s articles on initial page", len(initial_links))
        
        # Apply max_links limit consistently
        if max_links is not None and len(links) >= max_links:
            return link_extractor.truncate_links(links, max_links)
        
        # Step 2: Continue with AJAX pagination starting from page 2
        crawler.logger.info("Starting AJAX pagination from page %s", page_index)
        
        while True:
            if max_pages is not None and (page_index - 1) > max_pages:  # -1 because we start from page 2
                break
                
            # Check if we've reached the limit
            if max_links is not None and len(links) >= max_links:
                break
                
            # Fetch next page via AJAX
            ajax_html = self._fetch_ajax_page(
                crawler, page_index, nonce, ajax_url, action, view, nonce_param, base_url, ajax_config
            )
            if not ajax_html:
                crawler.logger.info("No more articles via AJAX at page %s, stopping.", page_index)
                break
            
            # Parse AJAX response
            ajax_soup = BeautifulSoup(ajax_html, "html.parser")
            ajax_links = self._parse_articles_from_soup(ajax_soup, link_extractor, site_config)
            
            if not ajax_links:
                crawler.logger.info("No new articles found in AJAX response at page %s, stopping.", page_index)
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
                        crawler.logger.info(
                            "Reached requested max_links=%s at AJAX page %s", max_links, page_index
                        )
                        return link_extractor.truncate_links(links, max_links)
            
            if len(links) == page_links_before:
                crawler.logger.info("No new unique articles found in AJAX response at page %s, stopping.", page_index)
                break
            
            crawler.logger.info(
                "Discovered %s total article links after AJAX page %s (%d new this page)", 
                len(links), page_index, len(ajax_links)
            )
            page_index += 1  # Increment to next page
        
        return link_extractor.truncate_links(links, max_links)
    
    def _extract_ajax_nonce(self, html: str, nonce_param: str, crawler: BaseCrawler, 
                         ajax_config: Dict[str, Any]) -> Optional[str]:
        """Extract AJAX nonce from the page HTML using config-driven patterns."""
        try:
            import re
            
            # Get nonce patterns from config or use defaults
            nonce_patterns = ajax_config.get('nonce_patterns', [
                rf'{nonce_param}["\']?\s*:\s*["\']([a-f0-9]+)["\']',
                rf'{nonce_param}["\']?\s*=\s*["\']([a-f0-9]+)["\']',
                rf'nonce["\']?\s*:\s*["\']([a-f0-9]+)["\']',
                rf'_ajax_nonce["\']?\s*:\s*["\']([a-f0-9]+)["\']',
                rf'nonce_ajax["\']?\s*=\s*{{[^}}]*{nonce_param}["\']?\s*:\s*["\']([a-f0-9]+)["\']',
            ])
            
            for pattern in nonce_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    nonce = match.group(1)
                    crawler.logger.info("Found AJAX nonce: %s", nonce)
                    return nonce
            
            # If not found in JS, try to find in meta tags or other locations
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for nonce in data attributes
            nonce_elem = soup.find(attrs={"data-nonce": True})
            if nonce_elem:
                nonce = nonce_elem.get("data-nonce")
                if nonce:
                    crawler.logger.info("Found AJAX nonce in data attribute: %s", nonce)
                    return nonce
            
            crawler.logger.warning("Could not find AJAX nonce in page HTML")
            return None
            
        except Exception as exc:
            crawler.logger.exception("Error extracting AJAX nonce: %s", exc)
            return None
    
    def _fetch_ajax_page(self, crawler: BaseCrawler, page: int, nonce: str, ajax_url: str, 
                         action: str, view: str, nonce_param: str, base_url: str,
                         ajax_config: Dict[str, Any]) -> Optional[str]:
        """Fetch articles via AJAX request with config-driven headers."""
        payload = {
            "action": action,
            "page": str(page),
            "view": view,
            nonce_param: nonce,
        }
        
        try:
            crawler.logger.info("Fetching AJAX page %s with payload: %s", page, payload)
            crawler.logger.info("AJAX URL: %s", ajax_url)
            
            # Get headers from config or use defaults
            config_headers = ajax_config.get('headers', {})
            default_headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
                "Referer": base_url,
                "Origin": "https://yhoccongdong.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }
            
            # Merge config headers with defaults (config takes precedence)
            headers = {**default_headers, **config_headers}
            
            # Update session headers for AJAX - match browser exactly
            original_headers = crawler.session.headers.copy()
            try:
                crawler.session.headers.update(headers)
                
                # Use POST request for AJAX
                import time
                time.sleep(crawler.delay_seconds)  # Respect delay
                
                resp = crawler.session.post(
                    ajax_url, 
                    data=payload, 
                    timeout=crawler.timeout_seconds
                )
                
                crawler.logger.info("AJAX POST response status: %s", resp.status_code)
                
                # If POST fails, try GET
                if resp.status_code != 200:
                    crawler.logger.warning("POST failed, trying GET method...")
                    get_params = payload.copy()
                    resp = crawler.session.get(
                        ajax_url, 
                        params=get_params, 
                        timeout=crawler.timeout_seconds
                    )
                    crawler.logger.info("AJAX GET response status: %s", resp.status_code)
            finally:
                # Always restore original headers
                crawler.session.headers = original_headers
            
            crawler.logger.info("AJAX response headers: %s", dict(resp.headers))
            
            if resp.status_code == 200:
                # Handle Brotli compression
                response_text = resp.text
                content_encoding = resp.headers.get('content-encoding', '').lower()
                
                if content_encoding == 'br':
                    try:
                        import brotli
                        # Decompress Brotli content
                        response_text = brotli.decompress(resp.content).decode('utf-8')
                        crawler.logger.info("Successfully decompressed Brotli response")
                    except Exception as e:
                        crawler.logger.error("Failed to decompress Brotli: %s", e)
                        # Try to decode as raw content first
                        try:
                            response_text = resp.content.decode('utf-8')
                            crawler.logger.info("Successfully decoded raw content as UTF-8")
                        except UnicodeDecodeError:
                            # Last resort: use resp.text (may be garbage but won't crash)
                            response_text = resp.text
                            crawler.logger.warning("Using resp.text as last resort for Brotli failure")
                
                crawler.logger.info("AJAX response content type: %s", resp.headers.get('content-type', 'unknown'))
                crawler.logger.info("AJAX response encoding: %s", content_encoding)
                crawler.logger.info("AJAX response length: %d chars", len(response_text))
                
                # The response should be HTML content, not JSON
                if response_text.strip():
                    # Check if it's HTML with article content
                    if '<article' in response_text or 'post-item' in response_text or 'class="post' in response_text:
                        crawler.logger.info("Got HTML response with article content")
                        return response_text
                    else:
                        crawler.logger.warning("Response doesn't contain expected article HTML")
                        crawler.logger.info("Full AJAX response for debugging:")
                        crawler.logger.info("=" * 50)
                        crawler.logger.info(response_text[:1000])  # First 1000 chars
                        crawler.logger.info("=" * 50)
                        return response_text
                else:
                    crawler.logger.warning("Got empty response from AJAX")
                    return None
            else:
                crawler.logger.warning("AJAX request failed with status %s", resp.status_code)
                # Try to get error details
                try:
                    error_text = resp.text[:500]  # First 500 chars
                    crawler.logger.warning("Error response: %s", error_text)
                except:
                    pass
                return None
                
        except Exception as exc:
            crawler.logger.exception("Error fetching AJAX page %s: %s", page, exc)
            return None
    
    def _parse_articles_from_soup(self, soup: BeautifulSoup, link_extractor: LinkExtractor, 
                                 site_config: Dict[str, Any]) -> List[ArticleLink]:
        """Parse article links from BeautifulSoup object using site-specific selectors."""
        links: List[ArticleLink] = []
        
        # Use site-specific selectors
        selectors_config = site_config.get('selectors', {})
        article_selectors = selectors_config.get('article_links', [])
        
        # Try each selector until we find articles
        for selector in article_selectors:
            candidates = soup.select(selector)
            if candidates:
                for element in candidates:
                    if hasattr(element, 'get') and element.get('href'):
                        link = link_extractor._process_element(element)
                        if link:
                            links.append(link)
                break  # Use first successful selector
        
        return links
