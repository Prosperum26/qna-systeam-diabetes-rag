"""Logging configuration for the crawler package."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for crawler module.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
