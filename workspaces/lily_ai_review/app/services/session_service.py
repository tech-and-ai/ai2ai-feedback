"""
Session service for managing user sessions.

This module provides a centralized way to manage user sessions, including
authentication, session data, and security features.
"""
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import Request

from app.logging import get_logger
from app.exceptions import AuthenticationError
from app.services.base_service import BaseService

# Get logger
logger = get_logger(__name__)

class SessionService(BaseService):
    """Service for managing user sessions."""

    def __init__(self):
        """Initialize the session service."""
        super().__init__()
        self.session_max_age = self.config.SESSION_MAX_AGE
        self.logger.info(f"Initializing session service with max age: {self.session_max_age} seconds")

    def is_authenticated(self, request: Request) -> bool:
        """
        Check if a user is authenticated.

        Args:
            request: The incoming request

        Returns:
            True if the user is authenticated, False otherwise
        """
        # Check if user_id exists in session
        if "user_id" not in request.session:
            return False

        # Check if session has expired
        if self._is_session_expired(request):
            logger.info("Session expired, clearing session data")
            self.clear_session(request)
            return False

        # Update last activity timestamp
        self._update_last_activity(request)

        return True

    def get_user_id(self, request: Request) -> Optional[str]:
        """
        Get the user ID from the session.

        Args:
            request: The incoming request

        Returns:
            User ID if authenticated, None otherwise
        """
        if not self.is_authenticated(request):
            return None

        return request.session.get("user_id")

    def get_user(self, request: Request) -> Dict[str, Any]:
        """
        Get the user data from the session.

        Args:
            request: The incoming request

        Returns:
            Dictionary containing user data
        """
        if not self.is_authenticated(request):
            return {}

        return {
            "id": request.session.get("user_id"),
            "email": request.session.get("email"),
            "username": request.session.get("username"),
            "subscription_tier": request.session.get("subscription_tier", "free"),
            "last_activity": request.session.get("last_activity"),
            "session_id": request.session.get("session_id")
        }

    def set_user(self, request: Request, user_data: Dict[str, Any]) -> None:
        """
        Set user data in the session.

        Args:
            request: The incoming request
            user_data: Dictionary containing user data
        """
        # Set basic user data
        request.session["user_id"] = user_data.get("id")
        request.session["email"] = user_data.get("email")
        request.session["username"] = user_data.get("username")
        request.session["subscription_tier"] = user_data.get("subscription_tier", "free")

        # Set session metadata
        request.session["session_id"] = str(uuid.uuid4())
        request.session["created_at"] = int(time.time())
        request.session["last_activity"] = int(time.time())

        # Set session fingerprint
        request.session["fingerprint"] = self._generate_fingerprint(request)

        logger.info(f"Session created for user: {user_data.get('email')}")

    def update_user(self, request: Request, user_data: Dict[str, Any]) -> None:
        """
        Update user data in the session.

        Args:
            request: The incoming request
            user_data: Dictionary containing user data to update
        """
        if not self.is_authenticated(request):
            logger.warning("Attempted to update session for unauthenticated user")
            return

        # Update user data
        for key, value in user_data.items():
            if key in ["user_id", "email", "username", "subscription_tier"]:
                request.session[key] = value

        # Update last activity
        self._update_last_activity(request)

        logger.info(f"Session updated for user: {request.session.get('email')}")

    def clear_session(self, request: Request) -> None:
        """
        Clear the session.

        Args:
            request: The incoming request
        """
        # Log the logout if user was authenticated
        if "user_id" in request.session:
            logger.info(f"Session cleared for user: {request.session.get('email')}")

        # Clear all session data
        request.session.clear()

    def validate_session(self, request: Request) -> bool:
        """
        Validate the session integrity.

        Args:
            request: The incoming request

        Returns:
            True if the session is valid, False otherwise
        """
        if not self.is_authenticated(request):
            return False

        # Check if fingerprint matches
        current_fingerprint = self._generate_fingerprint(request)
        stored_fingerprint = request.session.get("fingerprint")

        if not stored_fingerprint or current_fingerprint != stored_fingerprint:
            logger.warning("Session fingerprint mismatch, possible session hijacking attempt")
            self.clear_session(request)
            return False

        return True

    def require_auth(self, request: Request) -> Dict[str, Any]:
        """
        Require authentication for a request.

        Args:
            request: The incoming request

        Returns:
            User data if authenticated

        Raises:
            AuthenticationError: If the user is not authenticated
        """
        if not self.is_authenticated(request):
            raise AuthenticationError("Authentication required")

        if not self.validate_session(request):
            raise AuthenticationError("Invalid session")

        return self.get_user(request)

    def _is_session_expired(self, request: Request) -> bool:
        """
        Check if the session has expired.

        Args:
            request: The incoming request

        Returns:
            True if the session has expired, False otherwise
        """
        last_activity = request.session.get("last_activity")

        if not last_activity:
            return True

        current_time = int(time.time())
        return (current_time - last_activity) > self.session_max_age

    def _update_last_activity(self, request: Request) -> None:
        """
        Update the last activity timestamp.

        Args:
            request: The incoming request
        """
        request.session["last_activity"] = int(time.time())

    def _generate_fingerprint(self, request: Request) -> str:
        """
        Generate a fingerprint for the session.

        Args:
            request: The incoming request

        Returns:
            Session fingerprint
        """
        # Use user agent and other headers to generate a fingerprint
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        # Combine with user ID for a unique fingerprint
        user_id = request.session.get("user_id", "")

        # Simple fingerprint generation - in production, use a more secure method
        fingerprint = f"{user_id}:{user_agent}:{ip_address}"

        return fingerprint

def get_session_service() -> SessionService:
    """
    Get the session service instance.

    Returns:
        Session service instance
    """
    try:
        from app.services.dependency_container import get_container
        container = get_container()

        # Try to get the service from the container
        try:
            return container.get(SessionService)
        except KeyError:
            # Register the service if not found
            service = SessionService()
            container.register(SessionService, service)
            return service
    except ImportError:
        # Fall back to singleton pattern if dependency container is not available
        return SessionService.get_instance()

def get_session_user(request: Request) -> Dict[str, Any]:
    """
    Get the user data from the session.

    Args:
        request: The incoming request

    Returns:
        Dictionary containing user data
    """
    return get_session_service().get_user(request)
