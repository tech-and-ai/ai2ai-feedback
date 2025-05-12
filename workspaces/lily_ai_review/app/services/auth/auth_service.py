"""
Authentication service for interacting with Supabase auth.
"""
import os
import logging
from typing import Dict, Any, Optional

from app.services.supabase_service import get_supabase_client
from app.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class AuthService:
    """Service for interacting with Supabase auth."""

    def __init__(self):
        """Initialize the auth service."""
        self.supabase = get_supabase_client()

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their ID.

        Args:
            user_id: The user's ID

        Returns:
            The user data, or None if not found
        """
        try:
            # Get user from users_view (which mirrors auth.users)
            response = self.supabase.table("users_view").select("*").eq("id", user_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their email.

        Args:
            email: The user's email

        Returns:
            The user data, or None if not found
        """
        try:
            # Get user from users_view (which mirrors auth.users)
            response = self.supabase.table("users_view").select("*").eq("email", email).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
