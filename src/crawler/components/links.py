"""Link extraction and article link representation."""

from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag

from ..base import BaseCrawler
from ..utils.url import normalize_url


class ArticleLink:
    """Represents a discovered article link."""
    
    def __init__(self, title: str, url: str, category: str = "general"):
        self.title = title
        self.url = url
        self.category = category
    
    def __repr__(self):
        return f"ArticleLink(title='{self.title}', url='{self.url}', category='{self.category}')"


class LinkExtractor:
    """
    Handles extraction of article links from web pages.
    
    Uses configurable CSS selectors and category patterns.
    """
    
    def __init__(self, site_config: Dict[str, Any], crawler: BaseCrawler):
        """
        Initialize link extractor.
        
        Args:
            site_config: Site-specific configuration
            crawler: Crawler instance for logging
        """
        self.site_config = site_config
        self.crawler = crawler
        self.selectors_config = site_config.get('selectors', {})
        
        # Track seen URLs, titles, and content hashes to avoid duplicates
        self._seen_urls: set[str] = set()
        self._seen_titles: set[str] = set()
        self._seen_hashes: set[str] = set()
    
    def extract_links_from_page(self, soup: BeautifulSoup) -> List[ArticleLink]:
        """
        Extract article links from a BeautifulSoup page.
        
        Args:
            soup: Parsed HTML page
            
        Returns:
            List of ArticleLink objects
        """
        links: List[ArticleLink] = []
        
        # Get article links using configured selectors
        article_selectors = self.selectors_config.get('article_links', [])
        candidates = []
        
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                candidates.extend(elements)
                self.crawler.logger.debug("Found %d elements with selector '%s'", len(elements), selector)
                break  # Use first successful selector
        
        if not candidates:
            self.crawler.logger.warning("No article links found with any configured selector")
            return links
        
        # Process each candidate element
        for element in candidates:
            if not isinstance(element, Tag):
                continue
            
            link = self._process_element(element)
            if link:
                links.append(link)
        
        self.crawler.logger.info("Extracted %d unique article links from page", len(links))
        return links
    
    def _process_element(self, element: Tag) -> Optional[ArticleLink]:
        """
        Process a single HTML element to extract article link.
        
        Args:
            element: HTML element containing link
            
        Returns:
            ArticleLink object or None if invalid
        """
        href = element.get("href")
        if not href:
            return None
        
        # Normalize URL
        base_url = self.site_config.get('base_url', '')
        full_url = normalize_url(href, base_url)
        
        # Skip if already seen URL
        if full_url in self._seen_urls:
            self.crawler.logger.debug("Skipping already-seen URL: %s", full_url)
            return None
        
        # Extract title
        title = self._extract_title(element)
        if not title or title in self._seen_titles:
            return None
        
        # Generate content hash from element content
        content_hash = self._generate_content_hash(element)
        if content_hash and content_hash in self._seen_hashes:
            self.crawler.logger.debug("Skipping duplicate content hash: %s", content_hash)
            return None
        
        # Extract category
        category = self._extract_category(full_url)
        
        # Create article link
        article_link = ArticleLink(title=title, url=full_url, category=category)
        
        # Track to avoid duplicates
        self._seen_urls.add(full_url)
        self._seen_titles.add(title)
        if content_hash:
            self._seen_hashes.add(content_hash)
        
        return article_link
    
    def _extract_title(self, element: Tag) -> Optional[str]:
        """
        Extract clean title from element.
        
        Args:
            element: HTML element
            
        Returns:
            Clean title string or None
        """
        try:
            from processors import normalize_text
            title = normalize_text(element.get_text())
            return title if title and len(title.strip()) > 0 else None
        except Exception as e:
            self.crawler.logger.debug("Failed to extract title from element: %s", e)
            return None
    
    def _extract_category(self, url: str) -> str:
        """
        Extract category from URL using configured patterns.
        
        Args:
            url: Article URL
            
        Returns:
            Category string
        """
        default_category = self.site_config.get('default_category', 'general')
        category_patterns = self.selectors_config.get('category_patterns', {})
        
        # Check URL patterns
        for pattern, category in category_patterns.items():
            if pattern in url:
                return category
        
        return default_category
    
    def truncate_links(self, links: List[ArticleLink], max_links: Optional[int]) -> List[ArticleLink]:
        """
        Truncate links list to max_links if specified.
        
        Args:
            links: List of article links
            max_links: Maximum number of links to keep
            
        Returns:
            Truncated list of links
        """
        if max_links is not None and len(links) > max_links:
            self.crawler.logger.info("Truncating links from %d to %d", len(links), max_links)
            return links[:max_links]
        return links
    
    def _generate_content_hash(self, element: Tag) -> Optional[str]:
        """
        Generate content hash from element for duplicate detection.
        
        Args:
            element: HTML element containing link
            
        Returns:
            Content hash string or None if failed
        """
        try:
            import hashlib
            from processors import normalize_text
            
            # Get text content from element and nearby siblings
            content_parts = []
            
            # Add element text
            element_text = normalize_text(element.get_text())
            if element_text:
                content_parts.append(element_text)
            
            # Add title from nearby headings
            parent = element.parent
            if parent:
                # Look for heading elements near the link
                for heading in parent.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    heading_text = normalize_text(heading.get_text())
                    if heading_text and heading_text != element_text:
                        content_parts.append(heading_text)
                        break  # Use first heading found
            
            # Generate hash from combined content
            if content_parts:
                combined_content = " ".join(content_parts)
                content_hash = hashlib.md5(combined_content.encode('utf-8')).hexdigest()
                return content_hash
            
            return None
            
        except Exception as e:
            self.crawler.logger.debug("Failed to generate content hash: %s", e)
            return None
    
    def reset_tracking(self):
        """Reset tracking of seen URLs, titles, and content hashes."""
        self._seen_urls.clear()
        self._seen_titles.clear()
        self._seen_hashes.clear()
        self.crawler.logger.debug("Reset link tracking (URLs, titles, and hashes)")
