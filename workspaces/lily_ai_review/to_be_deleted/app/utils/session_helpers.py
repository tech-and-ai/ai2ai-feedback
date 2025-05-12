"""
Session helper functions for the Lily AI application.

This module provides utility functions for handling user sessions.
DEPRECATED: Use app.utils.session.SessionManager instead.
This module is kept for backward compatibility.
"""

import logging
from fastapi import Request
from typing import Dict, Optional, Any

from auth.models import User
from app.utils.session import get_session_manager

# Set up logging
logger = logging.getLogger(__name__)

# Get the session manager
session_manager = get_session_manager()


def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get the user data from the session.
    DEPRECATED: Use session_manager.get_session_user instead.

    Args:
        request: The incoming request

    Returns:
        A dictionary containing user data if the user is logged in, None otherwise
    """
    logger.warning("DEPRECATED: Use session_manager.get_session_user instead of get_session_user")
    return session_manager.get_session_user(request)


def set_session_user(request: Request, user: User) -> None:
    """
    Set the user data in the session.
    DEPRECATED: Use session_manager.set_session_user instead.

    Args:
        request: The incoming request
        user: The user to set in the session
    """
    logger.warning("DEPRECATED: Use session_manager.set_session_user instead of set_session_user")
    session_manager.set_session_user(request, user)


def clear_session(request: Request) -> None:
    """
    Clear the session data.
    DEPRECATED: Use session_manager.clear_session instead.

    Args:
        request: The incoming request
    """
    logger.warning("DEPRECATED: Use session_manager.clear_session instead of clear_session")
    session_manager.clear_session(request)


def update_user_session(request: Request, subscription_tier: str) -> bool:
    """
    Update the user's session with subscription information.
    DEPRECATED: Use session_manager.update_subscription_tier instead.

    Args:
        request: The incoming request
        subscription_tier: The subscription tier to set

    Returns:
        True if the session was updated successfully, False otherwise
    """
    logger.warning("DEPRECATED: Use session_manager.update_subscription_tier instead of update_user_session")
    return session_manager.update_subscription_tier(request, subscription_tier)
