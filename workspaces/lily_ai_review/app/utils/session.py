"""
Session management for Lily AI.

This module provides session management functionality.
"""

import logging
from typing import Dict, Any, Optional, Union
from fastapi import Request
from datetime import datetime

from auth.models import User
from auth.service import AuthService

# Set up logging
logger = logging.getLogger(__name__)

class SessionManager:
    """Session manager for Lily AI."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the SessionManager if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        """Initialize the SessionManager."""
        self.auth_service = AuthService()

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
            "name": request.session.get("name"),
            "subscription_tier": request.session.get("subscription_tier", "free"),
            "email_verified": request.session.get("email_verified", False),
            "is_admin": request.session.get("is_admin", False)
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
            # Ensure username is set
            username = user.username
            if not username:
                if user.name:
                    username = user.name.lower().replace(' ', '_')
                else:
                    username = user.email.split('@')[0]

            request.session["user_id"] = user.id
            request.session["email"] = user.email
            request.session["username"] = username
            request.session["name"] = user.name
            request.session["subscription_tier"] = user.subscription_tier
            request.session["email_verified"] = user.email_verified
            request.session["is_admin"] = user.is_admin

            # Check if session has a modified attribute (FastAPI's SessionMiddleware)
            if hasattr(request.session, 'modified'):
                request.session.modified = True

            logger.info(f"Set session user: {username} ({user.email})")
            return True
        except Exception as e:
            logger.error(f"Error setting session user: {str(e)}")
            # Fallback to basic session handling
            try:
                # Ensure username is set for fallback too
                username = user.username
                if not username:
                    if user.name:
                        username = user.name.lower().replace(' ', '_')
                    else:
                        username = user.email.split('@')[0]

                for key, value in {
                    "user_id": user.id,
                    "email": user.email,
                    "username": username,
                    "name": user.name,
                    "subscription_tier": user.subscription_tier,
                    "email_verified": user.email_verified,
                    "is_admin": user.is_admin
                }.items():
                    request.session[key] = value
                return True
            except Exception as fallback_error:
                logger.error(f"Error in fallback session handling: {str(fallback_error)}")
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
            logger.info("Session cleared")
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
            if hasattr(request.session, 'modified'):
                request.session.modified = True

            # Log the update
            logger.info(f"Updated session subscription_tier to {subscription_tier} for user {user_id}")

            # Update the user's metadata
            self.auth_service.update_user_metadata(user_id, {"subscription_tier": subscription_tier})

            # Update the subscription in the database
            try:
                from app.services.billing.subscription_service import SubscriptionService
                subscription_service = SubscriptionService()
                
                # Update the subscription
                subscription_service.update_subscription(
                    user_id=user_id,
                    tier=subscription_tier,
                    status="active",
                    papers_limit=10 if subscription_tier == "premium" else 0
                )
                
                logger.info(f"Updated subscription for user {user_id} with tier {subscription_tier}")
            except Exception as sub_error:
                logger.error(f"Error updating subscription: {str(sub_error)}")
                # Continue even if subscription update fails

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
