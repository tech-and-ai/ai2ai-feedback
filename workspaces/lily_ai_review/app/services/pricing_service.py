"""
Pricing Service

This module provides functions to retrieve pricing information from the database.
"""
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

class PricingService:
    """Service for retrieving pricing information from the database."""
    
    def __init__(self):
        """Initialize the pricing service."""
        self.supabase = get_supabase_client()
        logger.info("Pricing service initialized")
    
    @lru_cache(maxsize=10)
    def get_all_pricing_plans(self) -> List[Dict[str, Any]]:
        """
        Get all active pricing plans with their features.
        
        Returns:
            List of pricing plans with features
        """
        try:
            # Get all active pricing plans
            plans_result = self.supabase.table('saas_pricing_plans') \
                .select('*') \
                .eq('is_active', True) \
                .order('display_order') \
                .execute()
            
            plans = plans_result.data
            
            # Get features for each plan
            for plan in plans:
                features_result = self.supabase.table('saas_pricing_features') \
                    .select('*') \
                    .eq('plan_id', plan['id']) \
                    .order('display_order') \
                    .execute()
                
                plan['features'] = features_result.data
            
            return plans
        
        except Exception as e:
            logger.error(f"Error retrieving pricing plans: {str(e)}")
            return []
    
    @lru_cache(maxsize=10)
    def get_pricing_addons(self) -> List[Dict[str, Any]]:
        """
        Get all active pricing add-ons.
        
        Returns:
            List of pricing add-ons
        """
        try:
            result = self.supabase.table('saas_pricing_addons') \
                .select('*') \
                .eq('is_active', True) \
                .order('display_order') \
                .execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error retrieving pricing add-ons: {str(e)}")
            return []
    
    @lru_cache(maxsize=10)
    def get_pricing_display(self, section: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pricing display content.
        
        Args:
            section: Optional section name to filter by
            
        Returns:
            List of pricing display content
        """
        try:
            query = self.supabase.table('saas_pricing_display') \
                .select('*') \
                .eq('is_active', True)
            
            if section:
                query = query.eq('section', section)
            
            result = query.order('display_order').execute()
            
            return result.data
        
        except Exception as e:
            logger.error(f"Error retrieving pricing display content: {str(e)}")
            return []
    
    def format_currency(self, amount: float, currency: str = 'GBP') -> str:
        """
        Format a currency amount.
        
        Args:
            amount: The amount to format
            currency: The currency code
            
        Returns:
            Formatted currency string
        """
        if currency == 'GBP':
            return f"£{amount:.2f}"
        elif currency == 'USD':
            return f"${amount:.2f}"
        elif currency == 'EUR':
            return f"€{amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"
    
    def clear_cache(self):
        """Clear the cache for all methods."""
        self.get_all_pricing_plans.cache_clear()
        self.get_pricing_addons.cache_clear()
        self.get_pricing_display.cache_clear()


# Create a singleton instance
pricing_service = PricingService()
