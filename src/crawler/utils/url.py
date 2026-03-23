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
        # Parse base URL to extract domain and path
        base_parsed = urlparse(base_url)
        base_domain = f"{base_parsed.scheme}://{base_parsed.netloc}"
        base_path = base_parsed.path.rstrip('/')
        
        if url.startswith('/'):
            # Absolute path: /health-information/diabetes/overview/what-is-diabetes
            # Smart detection: check if URL already contains base_path
            if base_path and url.startswith(base_path + '/'):
                # URL already contains full path, use domain only
                return f"{base_domain}{url}"
            elif base_path and url == base_path:
                # URL matches base_path exactly
                return f"{base_domain}{url}"
            else:
                # URL doesn't contain base_path, use domain only
                return f"{base_domain}{url}"
        else:
            # Relative path: health-information/diabetes/overview/what-is-diabetes
            # Smart detection: check if relative URL already contains base_path components
            if base_path:
                # Split base_path and url into components
                base_components = base_path.split('/')
                url_components = url.split('/')
                
                # Check if URL starts with base_path components
                if (len(url_components) >= len(base_components) and 
                    url_components[:len(base_components)] == base_components):
                    # URL already contains base path, use domain + full url
                    return f"{base_domain}/{url}"
                else:
                    # URL doesn't contain base path, use domain + base_path + url
                    return f"{base_domain}/{base_path}/{url}"
            else:
                # No base path, use domain + url
                return f"{base_domain}/{url}"
    
    # If URL already has scheme and netloc, return as-is
    if parsed.scheme and parsed.netloc:
        return url
    
    # If URL has scheme but no netloc (unlikely), add netloc from base
    if parsed.scheme and not parsed.netloc and base_url:
        base_parsed = urlparse(base_url)
        return f"{parsed.scheme}://{base_parsed.netloc}{parsed.path}"
    
    # Default: return original URL
    return url


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
