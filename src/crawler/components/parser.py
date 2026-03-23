"""Document parsing logic for crawled articles."""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .links import ArticleLink
from ..utils.url import create_slug_from_url


class DocumentParser:
    """
    Handles parsing of HTML content into structured documents.
    
    Extracts titles, sections, and metadata from article HTML.
    """
    
    def __init__(self):
        """Initialize document parser."""
        pass
    
    def parse(self, article_link: ArticleLink, html: str) -> Optional[Dict[str, Any]]:
        """
        Parse article HTML into structured document.
        
        Args:
            article_link: Article link information
            html: Article HTML content
            
        Returns:
            Parsed document dictionary or None
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html, "html.parser")
            
            # Clean content
            self._clean_content(soup)
            
            # Split into sections
            sections = self._split_into_sections(soup)
            if not sections:
                return None
            
            # Extract title
            title = self._extract_title(soup, article_link.title)
            
            # Generate content hash
            content_hash = self._generate_content_hash(sections)
            
            # Create document
            document = {
                "doc_id": self._create_doc_id(article_link.url),
                "url": article_link.url,
                "title": title,
                "category": article_link.category,
                "sections": sections,
                "metadata": {
                    "crawl_time": datetime.now(timezone.utc).isoformat(),
                    "source_url": article_link.url,
                    "parser_type": "DocumentParser",
                    "content_hash": content_hash,
                    "total_sections": len(sections),
                    "content_length": sum(len(section.get("content", "")) for section in sections)
                }
            }
            
            return document
            
        except Exception as e:
            return None
    
    def _clean_content(self, soup: BeautifulSoup) -> None:
        """
        Clean HTML content by removing unwanted elements.
        
        Args:
            soup: BeautifulSoup object to clean
        """
        try:
            from processors import clean_article_soup
            clean_article_soup(soup)
        except Exception:
            # Fallback: remove common unwanted elements
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
    
    def _split_into_sections(self, soup: BeautifulSoup) -> list:
        """
        Split content into sections based on headings.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of section dictionaries
        """
        try:
            from processors import split_sections
            return split_sections(soup.body if soup.body else soup)
        except Exception:
            # Fallback: simple section extraction
            sections = []
            
            # Find all heading tags
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            if headings:
                for heading in headings:
                    title = heading.get_text().strip()
                    content = ""
                    
                    # Get content until next heading
                    next_element = heading.find_next_sibling()
                    while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        content += next_element.get_text().strip() + "\n"
                        next_element = next_element.find_next_sibling()
                    
                    if title and content:
                        sections.append({
                            "title": title,
                            "content": content.strip(),
                            "level": int(heading.name[1])  # h1=1, h2=2, etc.
                        })
            else:
                # No headings found, treat all content as one section
                body_text = soup.get_text().strip()
                if body_text:
                    sections.append({
                        "title": "Content",
                        "content": body_text,
                        "level": 1
                    })
            
            return sections
    
    def _extract_title(self, soup: BeautifulSoup, fallback_title: str) -> str:
        """
        Extract title from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            fallback_title: Fallback title from article link
            
        Returns:
            Extracted title string
        """
        try:
            from processors import normalize_text
            
            # Try h1 first
            title_elem = soup.find("h1")
            if title_elem:
                title = normalize_text(title_elem.get_text())
                if title:
                    return title
            
            # Try title tag
            if soup.title:
                title = normalize_text(soup.title.string)
                if title:
                    return title
            
            # Fallback
            return fallback_title
            
        except Exception:
            return fallback_title
    
    def _generate_content_hash(self, sections: list) -> str:
        """
        Generate content hash from document sections.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            MD5 hash string of normalized content
        """
        try:
            import hashlib
            from processors import normalize_text
            
            # Extract and normalize content from all sections
            content_parts = []
            for section in sections:
                content = section.get('content', '')
                if content:
                    normalized = normalize_text(content)
                    if normalized:
                        content_parts.append(normalized)
            
            if content_parts:
                # Sort content for consistent hashing regardless of order
                sorted_content = sorted(content_parts)
                combined_content = "\n".join(sorted_content)
                
                # Generate MD5 hash
                content_hash = hashlib.md5(combined_content.encode('utf-8')).hexdigest()
                return content_hash
            
            # Fallback hash for empty content
            return hashlib.md5(b"empty_content").hexdigest()
            
        except Exception:
            # Fallback hash if generation fails
            import hashlib
            return hashlib.md5(b"hash_generation_failed").hexdigest()
    
    def _create_doc_id(self, url: str) -> str:
        """
        Create document ID from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Document ID string
        """
        return create_slug_from_url(url)
