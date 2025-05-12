"""
Supabase client module.

This module provides a singleton instance of the Supabase client
that can be used throughout the application.
"""
import os
from typing import Optional
from functools import lru_cache
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Import the unified supabase client
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# We're now just re-exporting the get_supabase_client function from app.utils.supabase_client
# This maintains backward compatibility while using the unified implementation
