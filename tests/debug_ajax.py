#!/usr/bin/env python3
"""
Debug script for AJAX crawler with detailed logging.
"""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.impl import DiabetesCrawler, configure_logging


def debug_ajax_crawler():
    """Debug AJAX crawler with detailed logging."""
    print("=== DEBUG AJAX Crawler ===")
    
    # Configure debug logging
    configure_logging(logging.DEBUG)
    
    # Create crawler instance
    crawler = DiabetesCrawler(delay_seconds=1.0)
    
    print("\n1. Testing nonce extraction...")
    initial_html = crawler.fetch(crawler.BASE_CATEGORY_URL)
    if initial_html:
        nonce = crawler._extract_ajax_nonce(initial_html)
        print(f"Extracted nonce: {nonce}")
        
        if nonce:
            print("\n2. Testing AJAX request for page 2...")
            ajax_response = crawler._fetch_ajax_page(2, nonce)
            if ajax_response:
                print(f"Got AJAX response: {len(ajax_response)} characters")
                print(f"First 200 chars: {ajax_response[:200]}")
                
                # Try to parse articles
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(ajax_response, "html.parser")
                articles = crawler._parse_articles_from_soup(soup)
                print(f"Parsed {len(articles)} articles from AJAX response")
                for i, article in enumerate(articles[:3], 1):
                    print(f"  {i}. {article.title}")
            else:
                print("No AJAX response received")
        else:
            print("Could not extract nonce")
    else:
        print("Could not fetch initial page")


if __name__ == "__main__":
    debug_ajax_crawler()
