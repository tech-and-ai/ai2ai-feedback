"""
Authentication dependencies module.

This module provides FastAPI dependencies for authentication.
"""
from fastapi import Depends, HTTPException, status, Request, Header
from typing import Dict, Any, Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("ADMIN_API_KEY", "lily_api_key_default")

# Configure logging
logger = logging.getLogger(__name__)

async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Get the current authenticated user from the session or API key.

    Args:
        request: The incoming request with session data
        authorization: Optional authorization header for API key authentication

    Returns:
        Dict containing user data

    Raises:
        HTTPException: If user is not authenticated
    """
    # Check for API key in Authorization header
    if authorization:
        # Extract the token from the Authorization header (Bearer token format)
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")

            # Check if the token matches our admin API key
            if token == API_KEY:
                logger.info("API key authentication successful")

                # Return admin user data
                return {
                    "id": "55b4ec8c-2cf5-40fe-8718-75fe45f49a69",  # Admin user ID
                    "email": "pantaleone@btinternet.com",
                    "username": "admin",
                    "subscription_tier": "premium",
                    "is_admin": True
                }

    # If no API key or invalid API key, check session authentication
    if "user_id" not in request.session:
        logger.warning("Unauthenticated access attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Create user object from session data
    user = {
        "id": request.session.get("user_id"),
        "email": request.session.get("email"),
        "username": request.session.get("username"),
        "subscription_tier": request.session.get("subscription_tier", "free")
    }

    return user

async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the current authenticated admin user.

    Args:
        current_user: The current authenticated user

    Returns:
        Dict containing admin user data

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin"):
        logger.warning(f"Non-admin access attempt: {current_user.get('email')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user
