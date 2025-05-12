"""
Session helper utilities for managing user sessions.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import Request

# Configure logging
logger = logging.getLogger(__name__)

class SessionManager:
    """Session manager for handling user sessions."""
    
    def is_authenticated(self, request: Request) -> bool:
        """
        Check if a user is authenticated.
        
        Args:
            request: The incoming request
            
        Returns:
            True if the user is authenticated, False otherwise
        """
        return "user_id" in request.session
    
    def get_user_id(self, request: Request) -> Optional[str]:
        """
        Get the user ID from the session.
        
        Args:
            request: The incoming request
            
        Returns:
            User ID if authenticated, None otherwise
        """
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
            "subscription_tier": request.session.get("subscription_tier", "free")
        }
    
    def set_user(self, request: Request, user_data: Dict[str, Any]) -> None:
        """
        Set user data in the session.
        
        Args:
            request: The incoming request
            user_data: Dictionary containing user data
        """
        request.session["user_id"] = user_data.get("id")
        request.session["email"] = user_data.get("email")
        request.session["username"] = user_data.get("username")
        request.session["subscription_tier"] = user_data.get("subscription_tier", "free")
    
    def clear_session(self, request: Request) -> None:
        """
        Clear the session.
        
        Args:
            request: The incoming request
        """
        request.session.clear()

# Singleton instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """
    Get the session manager instance.
    
    Returns:
        Session manager instance
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager

def get_session_user(request: Request) -> Dict[str, Any]:
    """
    Get the user data from the session.
    
    Args:
        request: The incoming request
        
    Returns:
        Dictionary containing user data
    """
    return get_session_manager().get_user(request)
