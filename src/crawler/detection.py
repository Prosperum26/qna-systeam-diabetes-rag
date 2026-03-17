"""Site detection utility for crawler module."""

from typing import Dict, Any
from urllib.parse import urlparse


def detect_site_type(url: str, sites_config: Dict[str, Any]) -> str:
    """
    Detect site type from URL using sites configuration.
    
    Args:
        url: URL to analyze
        sites_config: Sites configuration dictionary
        
    Returns:
        Site type key (e.g., 'yhoccongdong', 'who', 'niddk', 'diabetes_org', 'generic')
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    sites = sites_config.get('sites', {})
    
    # Check exact domain matches
    for site_type, site_config in sites.items():
        base_url = site_config.get('base_url', '')
        if base_url and domain in base_url:
            return site_type
    
    # Fallback to domain-based detection
    if 'who.int' in domain:
        return 'who'
    elif 'niddk.nih.gov' in domain:
        return 'niddk'
    elif 'diabetes.org' in domain:
        return 'diabetes_org'
    elif 'yhoccongdong.com' in domain:
        return 'yhoccongdong'
    
    # Default fallback
    return 'generic'


def load_sites_config(config_path: str = "src/crawler/config/sites_config.json") -> Dict[str, Any]:
    """
    Load sites configuration for GenericCrawler.
    
    Args:
        config_path: Path to sites config file
        
    Returns:
        Sites configuration dictionary
    """
    import json
    import logging
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logging.info(f"Loaded sites config for {len(config.get('sites', {}))} sites")
        return config
        
    except FileNotFoundError:
        logging.error(f"Sites config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in sites config file: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error loading sites config: {e}")
        return {}
