"""URL utilities for the crawler package."""

import re
from urllib.parse import urlparse, urlunparse
from typing import Optional


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize URL according to site configuration.
    
    Args:
        url: URL to normalize
        base_url: Base URL for resolving relative URLs
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    # Parse URL
    parsed = urlparse(url)
    
    # Handle relative URLs
    if not parsed.scheme and not parsed.netloc and base_url:
        if url.startswith('/'):
            return f"{base_url.rstrip('/')}{url}"
        else:
            return f"{base_url.rstrip('/')}/{url}"
    
    # Normalize scheme and netloc
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or ""
    path = parsed.path
    
    # Remove default port
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    
    # Rebuild URL
    normalized = parsed._replace(scheme=scheme, netloc=netloc, path=path)
    final = urlunparse(normalized)
    
    if final.endswith("/") and final != "/":
        final = final.rstrip("/")
    
    return final


def create_slug_from_url(url: str) -> str:
    """
    Create a slug from URL for file naming.
    
    Args:
        url: URL to create slug from
        
    Returns:
        URL-safe slug string
    """
    try:
        parsed = urlparse(url)
        
        # Extract domain and path
        domain = parsed.netloc.replace("www.", "").replace(".", "_")
        path = parsed.path.strip("/").replace("/", "_")
        
        # Combine and clean
        slug = f"{domain}_{path}" if path else domain
        
        # Remove special characters
        slug = re.sub(r"[^a-zA-Z0-9_-]", "", slug)
        
        # Limit length
        if len(slug) > 100:
            slug = slug[:100]
        
        return slug.lower() or "unknown"
        
    except Exception:
        return "unknown"


def extract_nonce_from_page(nonce_param: str, html_content: str) -> Optional[str]:
    """
    Extract nonce value from HTML page JavaScript.
    
    Args:
        nonce_param: Parameter name for nonce
        html_content: HTML content to search in
        
    Returns:
        Nonce value if found, None otherwise
    """
    try:
        # Look for nonce in JavaScript variables
        pattern = rf'"{nonce_param}":"([^"]+)"'
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    except Exception:
        return None
