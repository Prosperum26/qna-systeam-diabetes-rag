"""Base crawler with core HTTP functionality."""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup

from .utils.logging import configure_logging


class BaseCrawler:
    """
    Base class providing core crawling functionality.
    
    Handles HTTP requests, retries, and basic content fetching.
    """
    
    def __init__(
        self,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        timeout_seconds: float = 15.0,
        session: Optional[requests.Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize base crawler.
        
        Args:
            delay_seconds: Delay between requests
            max_retries: Maximum retry attempts
            timeout_seconds: Request timeout
            session: Existing requests session
            logger: Logger instance
        """
        configure_logging()
        
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        # Configure session
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1"
        })
    
    def fetch(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch HTML content from URL with retry logic.
        
        Args:
            url: URL to fetch
            **kwargs: Additional request parameters
            
        Returns:
            HTML content as string, or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info("Fetching URL (attempt %d/%d): %s", attempt + 1, self.max_retries, url)
                
                # Add delay between requests
                if attempt > 0:
                    time.sleep(self.delay_seconds * (attempt + 1))
                else:
                    time.sleep(self.delay_seconds)
                
                # Make request
                response = self.session.get(
                    url, 
                    timeout=self.timeout_seconds,
                    **kwargs
                )
                
                # Check response
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type and 'text/plain' not in content_type:
                    self.logger.warning("Unexpected content type %s for %s", content_type, url)
                
                self.logger.info("Successfully fetched %s (%d bytes)", url, len(response.content))
                return response.text
                
            except requests.exceptions.RequestException as e:
                self.logger.warning("Request failed (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                if attempt == self.max_retries - 1:
                    self.logger.error("Failed to fetch %s after %d attempts", url, self.max_retries)
                    return None
            except Exception as e:
                self.logger.exception("Unexpected error fetching %s: %s", url, e)
                return None
        
        return None
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[str]:
        """
        Make POST request with retry logic.
        
        Args:
            url: URL to post to
            data: Form data to send
            **kwargs: Additional request parameters
            
        Returns:
            Response content as string, or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info("POST request (attempt %d/%d): %s", attempt + 1, self.max_retries, url)
                
                # Add delay between requests
                time.sleep(self.delay_seconds)
                
                # Make request
                response = self.session.post(
                    url,
                    data=data,
                    timeout=self.timeout_seconds,
                    **kwargs
                )
                
                # Check response
                response.raise_for_status()
                
                self.logger.info("POST successful for %s (%d bytes)", url, len(response.content))
                return response.text
                
            except requests.exceptions.RequestException as e:
                self.logger.warning("POST request failed (attempt %d/%d): %s", attempt + 1, self.max_retries, e)
                if attempt == self.max_retries - 1:
                    self.logger.error("Failed POST to %s after %d attempts", url, self.max_retries)
                    return None
            except Exception as e:
                self.logger.exception("Unexpected error POSTing to %s: %s", url, e)
                return None
        
        return None
    
    def save_raw_html(self, slug: str, html: str, base_dir: str = "data/raw") -> None:
        """
        Save raw HTML content to file.
        
        Args:
            slug: File slug
            html: HTML content
            base_dir: Base directory for saving
        """
        try:
            output_path = Path(base_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            file_path = output_path / f"{slug}.html"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.logger.info("Raw HTML saved: %s", file_path)
            
        except Exception as e:
            self.logger.exception("Failed to save raw HTML for %s: %s", slug, e)
    
    def save_document(self, slug: str, document: Dict[str, Any], base_dir: str = "data/documents") -> None:
        """
        Save processed document to JSON file.
        
        Args:
            slug: File slug
            document: Document dictionary
            base_dir: Base directory for saving
        """
        try:
            import json
            
            output_path = Path(base_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            file_path = output_path / f"{slug}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(document, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Document saved: %s", file_path)
            
        except Exception as e:
            self.logger.exception("Failed to save document for %s: %s", slug, e)
