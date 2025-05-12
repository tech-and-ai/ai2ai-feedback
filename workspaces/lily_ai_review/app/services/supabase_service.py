"""
Supabase service for interacting with the Supabase API.

This module provides a service for interacting with the Supabase API.
"""
from typing import Dict, Any, List, Optional, Union
import supabase
from supabase import create_client, Client

from app.config import config
from app.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Singleton instance
_supabase_client = None

def get_supabase_client() -> Client:
    """
    Get the Supabase client.
    
    Returns:
        Client: The Supabase client
    """
    global _supabase_client
    
    # If client already exists, return it
    if _supabase_client:
        return _supabase_client
        
    # Create client
    try:
        # Get Supabase URL and key
        url = config.SUPABASE_URL
        key = config.SUPABASE_KEY
        
        # Check if URL and key are provided
        if not url or not key:
            logger.error("Supabase URL or key not provided")
            raise ValueError("Supabase URL or key not provided")
            
        # Create client
        _supabase_client = create_client(url, key)
        
        # Log initialization
        logger.info("Initialized Supabase client")
        
        return _supabase_client
        
    except Exception as e:
        # Log error
        logger.error(f"Error initializing Supabase client: {str(e)}")
        
        # Raise error
        raise

class SupabaseService:
    """Service for interacting with the Supabase API."""
    
    def __init__(self):
        """Initialize the Supabase service."""
        # Get Supabase client
        self.client = get_supabase_client()
        
        # Log initialization
        logger.info("Initialized Supabase service")
        
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Optional[Dict[str, Any]]: The user, or None if not found
        """
        try:
            # Validate inputs
            if not user_id:
                logger.error("No user ID provided")
                return None
                
            # Query the user
            response = self.client.table("auth.users") \
                .select("*") \
                .eq("id", user_id) \
                .execute()
                
            # Check if user exists
            if not response.data or len(response.data) == 0:
                logger.warning(f"User not found: {user_id}")
                return None
                
            # Return the user
            return response.data[0]
            
        except Exception as e:
            # Log error
            logger.error(f"Error getting user: {str(e)}")
            
            # Return None
            return None
            
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email.
        
        Args:
            email: The email of the user
            
        Returns:
            Optional[Dict[str, Any]]: The user, or None if not found
        """
        try:
            # Validate inputs
            if not email:
                logger.error("No email provided")
                return None
                
            # Query the user
            response = self.client.table("auth.users") \
                .select("*") \
                .eq("email", email) \
                .execute()
                
            # Check if user exists
            if not response.data or len(response.data) == 0:
                logger.warning(f"User not found: {email}")
                return None
                
            # Return the user
            return response.data[0]
            
        except Exception as e:
            # Log error
            logger.error(f"Error getting user by email: {str(e)}")
            
            # Return None
            return None
