"""
Logging configuration for LLM module.

This module provides centralized logging configuration
for all LLM components.
"""

import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    include_timestamp: bool = True
) -> None:
    """
    Setup logging configuration for LLM module.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string
        include_timestamp: Whether to include timestamp in format
    """
    if format_string is None:
        if include_timestamp:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            format_string = "%(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger for the module
    logger = logging.getLogger("src.llm")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False
    
    logger.info(f"LLM module logging configured at level: {level}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"src.llm.{name}")
