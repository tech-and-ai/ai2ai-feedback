"""
Lily AI application.

This module provides the main application functionality.
"""

from app.auth import AuthService, get_auth_service, User, AuthResponse
from app.database import DatabaseClient, get_db_client
from app.utils import SessionManager, get_session_manager

__version__ = "0.1.0"

__all__ = [
    # Auth
    'AuthService', 'get_auth_service', 'User', 'AuthResponse',
    
    # Database
    'DatabaseClient', 'get_db_client',
    
    # Utils
    'SessionManager', 'get_session_manager',
]
