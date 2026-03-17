#!/usr/bin/env python3
"""
RAG Data Pipeline Crawler

This script orchestrates web crawling and document processing with two modes:
1. Config mode: Load URLs from JSON config file (default)
2. Single URL mode: Process a single URL with custom parameters

Usage:
    # Config mode (default)
    python -m src.pipelines.crawl_runner
    
    # Single URL mode
    python -m src.pipelines.crawl_runner --url https://example.com --category general --depth 2 --max-article 10
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler import DiabetesCrawler
from processors import clean_article_soup, normalize_text, split_sections


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def create_slug_from_url(url: str) -> str:
    """Create a safe filename slug from URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "_")
    
    if not path:
        path = "index"
    
    # Remove invalid characters
    safe_slug = "".join(c if c.isalnum() or c in "_-" else "_" for c in f"{domain}_{path}")
    return safe_slug[:100]  # Limit length


def load_url_config(config_path: str = "src/crawler/configURL.json") -> Dict[str, Any]:
    """
    Load URL configuration from JSON file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Filter enabled URLs
        enabled_urls = [url_config for url_config in config.get('urls', []) if url_config.get('enabled', True)]
        config['urls'] = enabled_urls
        
        logging.info(f"Loaded {len(enabled_urls)} enabled URLs from config")
        return config
        
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}


def process_single_url(url: str, crawler: DiabetesCrawler, output_dir: Path, 
                          category: str = "general", depth: int = 1, max_article: int = 5) -> bool:
    """
    Process a single URL and save as document.
    
    Args:
        url: URL to crawl
        crawler: DiabetesCrawler instance
        output_dir: Directory to save documents
        category: Category for the document
        depth: Crawling depth
        max_article: Maximum number of articles to extract
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Processing URL: {url} (category: {category}, depth: {depth}, max_article: {max_article})")
        
        # Step 1: Fetch HTML content using crawler
        html_content = crawler.fetch(url)
        if not html_content:
            logging.error(f"Failed to fetch HTML from: {url}")
            return False
        
        logging.info("HTML fetched successfully")
        
        # Step 2: Process HTML using processors
        logging.info("Extracting clean text")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Clean the article content
        clean_article_soup(soup)
        
        # Split into sections
        sections = split_sections(soup.body if soup.body else soup)
        if not sections:
            logging.warning(f"No sections extracted from: {url}")
            return False
        
        logging.info(f"Extracted {len(sections)} sections")
        
        # Step 3: Build document object
        logging.info("Building document object")
        
        # Extract title
        title = ""
        title_elem = soup.find("h1")
        if title_elem:
            title = normalize_text(title_elem.get_text())
        elif soup.title:
            title = normalize_text(soup.title.string)
        
        if not title:
            title = url  # Fallback to URL as title
        
        # Create document structure
        document = {
            "doc_id": create_slug_from_url(url),
            "url": crawler.normalize_url(url),
            "title": title,
            "category": category,
            "depth": depth,
            "max_article": max_article,
            "sections": sections,
            "metadata": {
                "crawl_time": datetime.now(timezone.utc).isoformat(),
                "source_url": url,
                "crawler_type": "single_url"
            }
        }
        
        # Step 4: Save document as JSON
        output_file = output_dir / f"{document['doc_id']}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Document saved to {output_file}")
        logging.info(f"Document saved successfully: {len(document['sections'])} sections")
        
        return True
        
    except Exception as e:
        logging.exception(f"Failed to process URL {url}: {e}")
        return False


def run_single_url(url: str, output_dir: str = "data/documents", 
                  category: str = "general", depth: int = 1, max_article: int = 5) -> None:
    """
    Run pipeline for a single URL.
    
    Args:
        url: Single URL to process
        output_dir: Directory to save documents
        category: Category for the document
        depth: Crawling depth
        max_article: Maximum number of articles to extract
    """
    logging.info("Starting single URL pipeline")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory: {output_path}")
    
    # Initialize crawler
    crawler = DiabetesCrawler(delay_seconds=2.0)
    
    # Process the single URL
    if process_single_url(url, crawler, output_path, category, depth, max_article):
        logging.info("Single URL pipeline completed successfully!")
    else:
        logging.error("Single URL pipeline failed!")


def run_config_mode(config: Dict[str, Any], output_dir: str = "data/documents") -> None:
    """
    Run pipeline using configuration file.
    
    Args:
        config: Configuration dictionary containing URLs and settings
        output_dir: Directory to save documents
    """
    urls = config.get('urls', [])
    global_settings = config.get('global_settings', {})
    
    logging.info("Starting config-based crawl pipeline")
    logging.info(f"URLs to process: {len(urls)}")
    
    if not urls:
        logging.error("No URLs found in configuration")
        return
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory: {output_path}")
    
    # Initialize crawler with config settings
    delay = global_settings.get('request_delay_seconds', 2.0)
    crawler = DiabetesCrawler(delay_seconds=delay)
    
    # Process each URL
    successful = 0
    failed = 0
    
    for i, url_config in enumerate(urls, 1):
        url = url_config['url']
        category = url_config.get('category', global_settings.get('default_category', 'general'))
        depth = url_config.get('depth', global_settings.get('default_depth', 1))
        max_article = url_config.get('max_article', global_settings.get('default_max_article', 5))
        
        logging.info(f"Processing URL {i}/{len(urls)}: {url} (category: {category}, depth: {depth}, max_article: {max_article})")
        
        if process_single_url(url, crawler, output_path, category, depth, max_article):
            successful += 1
        else:
            failed += 1
        
        # Add delay between requests
        if i < len(urls):
            logging.info("Waiting before next request...")
            import time
            time.sleep(delay)
    
    # Summary
    logging.info("Config-based crawl pipeline completed!")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")
    logging.info(f"Total: {len(urls)}")


def main() -> None:
    """Main entry point - orchestrates CLI and pipeline execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="RAG Data Pipeline Crawler with config and single URL modes"
    )
    
    # Mode selection
    parser.add_argument(
        "--url",
        help="Single URL to process (enables single URL mode)"
    )
    
    # Single URL mode parameters
    parser.add_argument(
        "--category",
        default="general",
        help="Category for single URL mode (default: general)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Crawling depth for single URL mode (default: 1)"
    )
    parser.add_argument(
        "--max-article",
        type=int,
        default=5,
        help="Maximum articles for single URL mode (default: 5)"
    )
    
    # Config mode parameters
    parser.add_argument(
        "--config",
        default="src/crawler/configURL.json",
        help="Path to URL configuration file (default: src/crawler/configURL.json)"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show loaded configuration and exit"
    )
    
    # Common parameters
    parser.add_argument(
        "--output-dir",
        default="data/documents",
        help="Output directory for documents (default: data/documents)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # Single URL mode
        if args.url:
            logging.info(f"Running in single URL mode for: {args.url}")
            run_single_url(
                url=args.url,
                output_dir=args.output_dir,
                category=args.category,
                depth=args.depth,
                max_article=args.max_article
            )
        else:
            # Config mode
            logging.info("Running in config mode")
            config = load_url_config(args.config)
            if not config:
                logging.error("Failed to load configuration")
                return
            
            # Show configuration if requested
            if args.show_config:
                print("Loaded configuration:")
                print(json.dumps(config, indent=2, ensure_ascii=False))
                return
            
            run_config_mode(config, args.output_dir)
            
    except KeyboardInterrupt:
        logging.info("Pipeline interrupted by user")
    except Exception as e:
        logging.exception(f"Pipeline failed: {e}")


if __name__ == "__main__":
    main()
