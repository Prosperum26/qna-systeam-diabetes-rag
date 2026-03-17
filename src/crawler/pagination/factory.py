"""Factory for creating pagination strategies."""

from typing import Dict, Any

from .strategies import PaginationStrategy, TraditionalPagination, AjaxPagination


class PaginationFactory:
    """Factory for creating pagination strategies."""
    
    @staticmethod
    def create_strategy(site_config: Dict[str, Any]) -> PaginationStrategy:
        """
        Create appropriate pagination strategy based on configuration.
        
        Args:
            site_config: Site configuration
            
        Returns:
            PaginationStrategy instance
        """
        pagination_config = site_config.get('pagination', {})
        pagination_type = pagination_config.get('type', 'traditional')
        
        if pagination_type == 'ajax':
            return AjaxPagination()
        else:
            return TraditionalPagination()
