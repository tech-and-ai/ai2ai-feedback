"""
Supabase client for authentication.
"""
from typing import Optional
from supabase import create_client, Client

from app.config import config
from app.logging import get_logger

# Get logger
logger = get_logger(__name__)

# Global client instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.

    Returns:
        Supabase client
    """
    global _supabase_client

    if _supabase_client is None:
        # Get Supabase credentials from configuration
        supabase_url = config.SUPABASE_URL if hasattr(config, 'SUPABASE_URL') else None
        supabase_key = config.SUPABASE_KEY if hasattr(config, 'SUPABASE_KEY') else None

        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in configuration")
            raise ValueError("Supabase credentials not found in configuration")

        # Create Supabase client
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Created Supabase client")

    return _supabase_client
