#!/usr/bin/env python3
"""
Test script for AJAX-based diabetes crawler.
This script demonstrates how to use the updated crawler with AJAX pagination.
"""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.crawler.scraper import run_diabetes_crawler
from src.crawler.impl import DiabetesCrawler, configure_logging


def test_ajax_crawler():
    """Test the AJAX crawler with a small number of articles."""
    print("Testing AJAX-based diabetes crawler...")
    
    # Configure logging
    configure_logging(logging.INFO)
    
    # Create crawler instance
    crawler = DiabetesCrawler(delay_seconds=1.0)  # Faster for testing
    
    # Test getting article links with AJAX
    print("\n=== Testing AJAX link discovery ===")
    links = crawler.get_article_links(max_pages=2, max_links=5, use_ajax=True)
    print(f"Found {len(links)} articles via AJAX:")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link.title}")
        print(f"   URL: {link.url}")
        print()
    
    # Test getting article links with traditional pagination (for comparison)
    print("\n=== Testing traditional pagination (for comparison) ===")
    traditional_links = crawler.get_article_links(max_pages=2, max_links=5, use_ajax=False)
    print(f"Found {len(traditional_links)} articles via traditional pagination:")
    for i, link in enumerate(traditional_links, 1):
        print(f"{i}. {link.title}")
        print(f"   URL: {link.url}")
        print()


def test_full_crawl():
    """Test full crawl with AJAX."""
    print("\n=== Testing full crawl with AJAX ===")
    
    # Run a small crawl with AJAX
    run_diabetes_crawler(max_articles=3, base_dir="test_data", use_ajax=True)
    
    print("Full crawl completed. Check 'test_data' directory for results.")


if __name__ == "__main__":
    print("Diabetes AJAX Crawler Test")
    print("=" * 50)
    
    try:
        # Test link discovery
        test_ajax_crawler()
        
        # Test full crawl
        test_full_crawl()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
