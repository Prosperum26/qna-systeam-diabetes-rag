"""Generic crawler with config-driven approach."""

from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from .base import BaseCrawler
from .components.links import LinkExtractor, ArticleLink
from .pagination.factory import PaginationFactory
from .utils.url import normalize_url


class GenericCrawler(BaseCrawler):
    """
    Config-driven generic crawler that can handle multiple websites.
    
    Uses site-specific configuration for CSS selectors and pagination rules.
    """
    
    def __init__(
        self,
        site_config: Dict[str, Any],
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> None:
        """
        Initialize generic crawler.
        
        Args:
            site_config: Site-specific configuration
            delay_seconds: Delay between requests
            max_retries: Maximum retry attempts
            timeout_seconds: Request timeout
            session: Existing requests session
            logger: Logger instance
        """
        super().__init__(
            delay_seconds=delay_seconds,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            session=session,
            logger=logger,
        )
        
        self.site_config = site_config
        self.link_extractor = LinkExtractor(site_config, self)
        self.pagination_strategy = PaginationFactory.create_strategy(site_config)
        
        # Track seen content hashes for document-level duplicate detection
        self._seen_document_hashes: set[str] = set()
        
        self.logger.info(f"Initialized GenericCrawler for {site_config.get('base_url', 'unknown site')}")
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL according to site configuration.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized absolute URL
        """
        base_url = self.site_config.get('base_url', '')
        return normalize_url(url, base_url)
    
    def get_article_links(
        self,
        max_pages: Optional[int] = None,
        max_links: Optional[int] = None,
    ) -> List[ArticleLink]:
        """
        Discover article links using configured pagination strategy.
        
        Args:
            max_pages: Maximum number of pages to crawl
            max_links: Maximum number of links to collect
            
        Returns:
            List of unique ArticleLink objects
        """
        self.logger.info(f"Discovering article links (max_pages={max_pages}, max_links={max_links})")
        
        # Reset tracking for fresh discovery
        self.link_extractor.reset_tracking()
        
        # Get links using pagination strategy
        links = self.pagination_strategy.get_links(
            crawler=self,
            link_extractor=self.link_extractor,
            max_pages=max_pages,
            max_links=max_links
        )
        
        self.logger.info(f"Discovered {len(links)} article links total")
        return links
    
    def crawl_category(
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
        self.logger.info(f"Starting category crawl (max_pages={max_pages}, max_links={max_links})")
        
        # Discover article links
        article_links = self.get_article_links(max_pages=max_pages, max_links=max_links)
        
        if not article_links:
            self.logger.warning("No article links discovered")
            return 0
        
        # Process each article
        processed = 0
        failed = 0
        
        for i, article_link in enumerate(article_links, 1):
            self.logger.info(f"Processing article {i}/{len(article_links)}: {article_link.url}")
            
            try:
                # Fetch article content
                html = self.fetch(article_link.url)
                if not html:
                    self.logger.error(f"Failed to fetch article: {article_link.url}")
                    failed += 1
                    continue
                
                # Parse and save document
                document = self.parse_article(article_link, html)
                if document:
                    # Check for duplicate content
                    if self._is_duplicate_document(article_link.url, document):
                        self.logger.info(f"Skipping duplicate document: {article_link.url}")
                        failed += 1
                        continue
                    
                    self.save_document(document['doc_id'], document, base_dir)
                    processed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                self.logger.exception(f"Error processing article {article_link.url}: {e}")
                failed += 1
        
        self.logger.info(f"Category crawl completed: {processed} successful, {failed} failed")
        return processed
    
    def parse_article(self, article_link: ArticleLink, html: str) -> Optional[Dict[str, Any]]:
        """
        Parse article HTML into structured document.
        
        Args:
            article_link: Article link information
            html: Article HTML content
            
        Returns:
            Parsed document dictionary or None
        """
        try:
            from .components.parser import DocumentParser
            
            # Use dedicated parser
            parser = DocumentParser()
            return parser.parse(article_link, html)
            
        except Exception as e:
            self.logger.exception(f"Failed to parse article {article_link.url}: {e}")
            return None
    
    def _is_duplicate_document(self, url: str, document: Dict[str, Any]) -> bool:
        """
        Check if document is duplicate based on content hash.
        
        Args:
            url: Document URL
            document: Parsed document dictionary
            
        Returns:
            True if duplicate, False otherwise
        """
        try:
            # Get hash from document metadata (generated by DocumentParser)
            content_hash = document.get('metadata', {}).get('content_hash')
            
            if not content_hash:
                self.logger.warning(f"No content hash found in document metadata for {url}")
                return False
            
            # Check if already seen
            if content_hash in self._seen_document_hashes:
                self.logger.debug(f"Duplicate content hash found: {content_hash}")
                return True
            
            # Add to seen hashes
            self._seen_document_hashes.add(content_hash)
            self.logger.debug(f"Added new content hash: {content_hash}")
            
            return False
            
        except Exception as e:
            self.logger.exception(f"Error checking duplicate document: {e}")
            return False
    
    def _detect_site_type(self) -> str:
        """Detect site type from configuration."""
        base_url = self.site_config.get('base_url', '')
        parsed = urlparse(base_url)
        domain = parsed.netloc.lower()
        
        if 'yhoccongdong.com' in domain:
            return 'yhoccongdong'
        elif 'who.int' in domain:
            return 'who'
        elif 'niddk.nih.gov' in domain:
            return 'niddk'
        elif 'diabetes.org' in domain:
            return 'diabetes_org'
        else:
            return 'generic'
