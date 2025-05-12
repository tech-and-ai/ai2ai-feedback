"""
Authentication models for the SaaS framework.

This module provides data models for authentication.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class User(BaseModel):
    """User model."""
    id: str
    email: EmailStr
    username: Optional[str] = None
    name: Optional[str] = None
    subscription_tier: str = "free"
    email_verified: bool = False
    is_admin: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_metadata: Optional[Dict[str, Any]] = None
    app_metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_supabase_user(cls, user_data: Dict[str, Any]) -> 'User':
        """
        Create a User instance from Supabase user data.

        Args:
            user_data: The Supabase user data

        Returns:
            A User instance
        """
        # Extract metadata
        user_metadata = user_data.get('raw_user_meta_data', {}) or {}
        app_metadata = user_data.get('app_metadata', {}) or {}

        # Extract email verification status
        email_verified = app_metadata.get('email_confirmed', False)

        # Extract username and name from metadata
        username = user_metadata.get('username')
        name = user_metadata.get('name')

        # For Google OAuth users, use the name as username if username is not set
        if not username:
            if name:
                # Convert name to a valid username (lowercase, replace spaces with underscores)
                username = name.lower().replace(' ', '_')
            elif user_data.get('email'):
                # If no name, use email prefix as username
                username = user_data.get('email').split('@')[0]

        # Extract subscription tier
        subscription_tier = user_metadata.get('subscription_tier', 'free')

        # Extract timestamps
        created_at = user_data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        updated_at = user_data.get('updated_at')
        if isinstance(updated_at, str) and updated_at:
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        else:
            updated_at = None

        return cls(
            id=user_data.get('id'),
            email=user_data.get('email'),
            username=username,
            name=name,
            subscription_tier=subscription_tier,
            email_verified=email_verified,
            is_admin=app_metadata.get('is_admin', False),
            created_at=created_at,
            updated_at=updated_at,
            user_metadata=user_metadata,
            app_metadata=app_metadata
        )

class AuthResponse(BaseModel):
    """Authentication response model."""
    user: Optional[User] = None
    error: Optional[str] = None
    success: bool = Field(default_factory=lambda: False)

    @property
    def is_success(self) -> bool:
        """
        Check if the authentication was successful.

        Returns:
            True if successful, False otherwise
        """
        return self.success and self.user is not None and self.error is None

    @classmethod
    def success_response(cls, user: User) -> 'AuthResponse':
        """
        Create a successful authentication response.

        Args:
            user: The authenticated user

        Returns:
            An AuthResponse instance
        """
        return cls(user=user, success=True)

    @classmethod
    def error_response(cls, error: str) -> 'AuthResponse':
        """
        Create an error authentication response.

        Args:
            error: The error message

        Returns:
            An AuthResponse instance
        """
        return cls(error=error, success=False)
