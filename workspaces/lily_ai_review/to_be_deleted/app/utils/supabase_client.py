"""
Supabase client utility module.
Provides functions to interact with Supabase.
"""
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from functools import lru_cache

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.
    
    Returns:
        Supabase Client object
    """
    try:
        # Check for multiple possible environment variable names for compatibility
        supabase_url = (
            os.getenv("SUPABASE_URL") or 
            os.getenv("SUPABASE_PROJECT_URL") or 
            "https://example.supabase.co"
        )
        
        supabase_key = (
            os.getenv("SUPABASE_KEY") or 
            os.getenv("SUPABASE_API_KEY") or 
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJvbGUiOiJhbm9uIiwiaWF0IjoxNjk5OTIwNjAwLCJleHAiOjIwMTU0OTY2MDB9.test_key_for_development"
        )
        
        # Log warning if using default values
        if supabase_url == "https://example.supabase.co":
            logger.warning("Using default Supabase URL. Set SUPABASE_URL or SUPABASE_PROJECT_URL for production.")
        if "test_key_for_development" in supabase_key:
            logger.warning("Using default Supabase key. Set SUPABASE_KEY or SUPABASE_API_KEY for production.")
        
        client = create_client(supabase_url, supabase_key)
        logger.info(f"Supabase client initialized with URL: {supabase_url[:20]}...")
        return client
    
    except Exception as e:
        logger.error(f"Error creating Supabase client: {str(e)}")
        raise 