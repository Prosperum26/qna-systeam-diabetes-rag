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
        """Get links using AJAX pagination."""
        links: List[ArticleLink] = []
        site_config = link_extractor.site_config
        ajax_config = site_config.get('pagination', {}).get('ajax', {})
        
        if not ajax_config:
            crawler.logger.warning("AJAX configuration not found, falling back to traditional pagination")
            # Fallback to traditional pagination
            traditional = TraditionalPagination()
            return traditional.get_links(crawler, link_extractor, max_pages, max_links)
        
        # Get initial page content
        base_url = site_config.get('base_url', '')
        html = crawler.fetch(base_url)
        if not html:
            crawler.logger.warning("Failed to fetch initial page for AJAX pagination")
            traditional = TraditionalPagination()
            return traditional.get_links(crawler, link_extractor, max_pages, max_links)
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract initial article links
        initial_links = link_extractor.extract_links_from_page(soup)
        links.extend(initial_links)
        
        # Get AJAX configuration
        ajax_url = ajax_config.get('ajax_url')
        action = ajax_config.get('action', 'watch_more_ar')
        view = ajax_config.get('view', 'cancer-default')
        nonce_param = ajax_config.get('nonce_param', '_ajax_nonce')
        current_page = ajax_config.get('initial_page', 1)
        max_pages = max_pages or 5  # Default limit for AJAX
        
        crawler.logger.info("Starting AJAX pagination from page %d", current_page)
        
        while current_page < max_pages and (max_links is None or len(links) < max_links):
            # Build AJAX request data (based on actual headers/payload)
            ajax_data = {
                'action': action,
                'page': str(current_page + 1),  # Page starts from 2
                'view': view
            }
            
            # Add nonce if configured
            if nonce_param:
                from ..utils.url import extract_nonce_from_page
                nonce = extract_nonce_from_page(nonce_param, html)
                if nonce:
                    ajax_data[nonce_param] = nonce
                else:
                    # Try to extract nonce from JavaScript variables
                    import re
                    nonce_pattern = rf'"{nonce_param}":"([^"]+)"'
                    nonce_match = re.search(nonce_pattern, html)
                    if nonce_match:
                        ajax_data[nonce_param] = nonce_match.group(1)
            
            # Make AJAX request with proper headers
            if not ajax_url:
                crawler.logger.warning("No AJAX URL configured")
                break
            
            # Set proper headers for AJAX request (based on actual headers)
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://yhoccongdong.com',
                'Referer': f'https://yhoccongdong.com/tieu-duong/page/{current_page}/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin'
            }
            
            try:
                ajax_html = crawler.session.post(
                    ajax_url, 
                    data=ajax_data, 
                    headers=headers,
                    timeout=crawler.timeout_seconds
                )
                
                if ajax_html.status_code == 200:
                    crawler.logger.info(f"AJAX request successful for page {current_page + 1}")
                    
                    # Parse AJAX response
                    ajax_soup = BeautifulSoup(ajax_html.text, "html.parser")
                    ajax_links = link_extractor.extract_links_from_page(ajax_soup)
                    
                    if not ajax_links:
                        crawler.logger.info("No more links found via AJAX, stopping pagination")
                        break
                    
                    links.extend(ajax_links)
                    crawler.logger.info("Found %d links via AJAX page %d (total: %d)", 
                                      len(ajax_links), current_page + 1, len(links))
                    
                    # Stop if max_links reached
                    if max_links is not None and len(links) >= max_links:
                        break
                        
                else:
                    crawler.logger.warning(f"AJAX request failed with status {ajax_html.status_code}")
                    break
                    
            except Exception as e:
                crawler.logger.exception(f"Error during AJAX pagination: {e}")
                break
            
            current_page += 1
        
        return link_extractor.truncate_links(links, max_links)
