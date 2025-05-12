"""
Session management for Lily AI.

This module provides session management functionality.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Request

from app.auth import get_auth_service, User

# Set up logging
logger = logging.getLogger(__name__)

class SessionManager:
    """Session manager for Lily AI."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the SessionManager if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance

    def get_session_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get the user data from the session.

        Args:
            request: The incoming request

        Returns:
            A dictionary containing user data if the user is logged in, None otherwise
        """
        if "user_id" not in request.session:
            return None

        return {
            "id": request.session.get("user_id"),
            "email": request.session.get("email"),
            "username": request.session.get("username"),
            "subscription_tier": request.session.get("subscription_tier", "free")
        }

    def set_session_user(self, request: Request, user: User) -> bool:
        """
        Set the user data in the session.

        Args:
            request: The incoming request
            user: The user to set in the session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if session is a dict or has a __setitem__ method
            if hasattr(request.session, "__setitem__"):
                request.session["user_id"] = user.id
                request.session["email"] = user.email
                request.session["username"] = user.username or user.email.split('@')[0]
                request.session["subscription_tier"] = user.subscription_tier

                # Mark the session as modified to ensure it's saved
                if hasattr(request.session, "modified"):
                    request.session.modified = True
            else:
                # If session is a dict-like object
                session_dict = dict(request.session)
                session_dict["user_id"] = user.id
                session_dict["email"] = user.email
                session_dict["username"] = user.username or user.email.split('@')[0]
                session_dict["subscription_tier"] = user.subscription_tier

                # Update the session
                for key, value in session_dict.items():
                    request.session[key] = value

            return True
        except Exception as e:
            logger.error(f"Error setting session user: {str(e)}")
            return False

    def clear_session(self, request: Request) -> bool:
        """
        Clear the session.

        Args:
            request: The incoming request

        Returns:
            True if successful, False otherwise
        """
        try:
            request.session.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return False

    def update_subscription_tier(self, request: Request, subscription_tier: str) -> bool:
        """
        Update the subscription tier in the session.

        Args:
            request: The incoming request
            subscription_tier: The subscription tier to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the user ID from the session
            user_id = request.session.get("user_id")
            if not user_id:
                logger.error("No user ID in session")
                return False

            # Update the session with the new subscription tier
            request.session["subscription_tier"] = subscription_tier

            # Mark the session as modified to ensure it's saved
            request.session.modified = True

            # Update the user's metadata
            auth_service = get_auth_service()
            auth_service.update_user_metadata(user_id, {"subscription_tier": subscription_tier})

            return True
        except Exception as e:
            logger.error(f"Error updating subscription tier in session: {str(e)}")
            return False

    def is_authenticated(self, request: Request) -> bool:
        """
        Check if the user is authenticated.

        Args:
            request: The incoming request

        Returns:
            True if authenticated, False otherwise
        """
        return "user_id" in request.session

    def get_subscription_tier(self, request: Request) -> str:
        """
        Get the subscription tier from the session.

        Args:
            request: The incoming request

        Returns:
            The subscription tier
        """
        return request.session.get("subscription_tier", "free")

# Create a singleton instance
session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """
    Get the session manager singleton.

    Returns:
        The session manager
    """
    return session_manager
