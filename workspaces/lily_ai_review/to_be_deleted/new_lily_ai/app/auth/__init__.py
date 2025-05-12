"""
Authentication module for Lily AI.

This module provides authentication functionality.
"""

from app.auth.service import AuthService, get_auth_service
from app.auth.models import User, AuthResponse

__all__ = ['AuthService', 'get_auth_service', 'User', 'AuthResponse']
