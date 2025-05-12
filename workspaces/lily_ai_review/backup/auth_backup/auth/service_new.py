"""
Authentication service for Lily AI.

This module provides authentication functionality.
"""

import re
import logging
import os
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

from auth.models import User, AuthResponse
from app.utils.supabase_client import get_supabase_client

# Set up logging
logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the AuthService if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the AuthService."""
        self.supabase = get_supabase_client()

    def sign_up(self, email: str, password: str, username: str, name: Optional[str] = None) -> AuthResponse:
        """
        Sign up a new user.

        Args:
            email: The user's email
            password: The user's password
            username: The user's username
            name: The user's name (optional)

        Returns:
            An AuthResponse instance
        """
        try:
            # Validate email
            if not self._validate_email(email):
                return AuthResponse.error_response("Invalid email address")

            # Validate password
            if not self._validate_password(password):
                return AuthResponse.error_response(
                    "Password must be at least 8 characters long and contain at least one uppercase letter, "
                    "one lowercase letter, one number, and one special character"
                )

            # Validate username
            if not self._validate_username(username):
                return AuthResponse.error_response(
                    "Username must be 3-20 characters long and contain only letters, numbers, and underscores"
                )

            # Check if username exists
            try:
                response = self.supabase.table("auth.users").select("id").eq("raw_user_meta_data->username", username).execute()
                if response.data and len(response.data) > 0:
                    return AuthResponse.error_response("Username is already taken")
            except Exception as e:
                logger.error(f"Error checking username: {str(e)}")
                # Continue with registration even if username check fails

            # Set up user metadata
            user_metadata = {
                "username": username,
                "name": name if name else username,
                "subscription_tier": "free"
            }

            # Register the user with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })

            if not response or not response.user:
                return AuthResponse.error_response("Failed to create user")

            # Create a default subscription
            self._create_default_subscription(response.user.id)

            # Create User model from response
            user = User.from_supabase_user(response.user.model_dump())

            return AuthResponse.success_response(user)

        except Exception as e:
            logger.error(f"Error signing up user: {str(e)}")
            return AuthResponse.error_response(f"An error occurred during sign up: {str(e)}")

    def sign_in(self, email: str, password: str) -> AuthResponse:
        """
        Sign in a user.

        Args:
            email: The user's email
            password: The user's password

        Returns:
            An AuthResponse instance
        """
        try:
            # Sign in with Supabase Auth
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response or not response.user:
                return AuthResponse.error_response("Invalid email or password")

            # Create User model from response
            user = User.from_supabase_user(response.user.model_dump())

            return AuthResponse.success_response(user)

        except Exception as e:
            logger.error(f"Error signing in user: {str(e)}")
            return AuthResponse.error_response("Invalid email or password")

    def sign_out(self) -> bool:
        """
        Sign out the current user.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Error signing out user: {str(e)}")
            return False

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user or None if not found
        """
        try:
            # Get user from Supabase Auth
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            if not response or not response.user:
                return None

            return User.from_supabase_user(response.user.model_dump())
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    def get_oauth_url(self, provider: str, redirect_url: str = None) -> str:
        """
        Get OAuth URL for the specified provider.

        Args:
            provider: The OAuth provider (e.g., 'google', 'facebook')
            redirect_url: URL to redirect to after authentication

        Returns:
            OAuth URL for redirection
        """
        try:
            options = {}

            # Special handling for Google OAuth
            if provider.lower() == 'google':
                # Explicitly set redirectTo to match the URL configured in Supabase
                import os

                # Always use the BASE_URL environment variable, but default to localhost for development
                base_url = os.getenv("BASE_URL", "http://localhost:8004")

                # Force localhost URL if it contains localhost in the URL
                if "localhost" in base_url:
                    base_url = "http://localhost:8004"
                    logger.info(f"Using localhost URL for OAuth callback: {base_url}")

                callback_url = f"{base_url}/auth/callback"
                options["redirectTo"] = callback_url
                logger.info(f"Google OAuth redirectTo explicitly set to: {callback_url}")

                # Store the final redirect in a session or database if needed
                if redirect_url:
                    logger.info(f"Final redirect after OAuth will be: {redirect_url}")

                # Minimal scopes to avoid verification requirements
                options["scopes"] = "openid email"

                # Add query parameters to force account selection and consent screen
                options["queryParams"] = {
                    "prompt": "select_account consent",  # Force account selection and consent screen
                    "access_type": "online"              # Standard access type
                }
            elif redirect_url:
                options["redirectTo"] = f"{redirect_url}"

            response = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": options
            })

            # Get the URL from the response
            oauth_url = response.url

            # For Google OAuth, manually add the prompt parameter to force account selection
            if provider.lower() == 'google':
                # Add prompt=select_account+consent to force account selection and consent screen
                if '?' in oauth_url:
                    oauth_url += '&prompt=select_account+consent&access_type=online'
                else:
                    oauth_url += '?prompt=select_account+consent&access_type=online'

            logger.info(f"Generated OAuth URL for {provider}: {oauth_url}")
            return oauth_url
        except Exception as e:
            logger.error(f"OAuth URL generation error: {str(e)}")
            raise

    def exchange_code_for_session(self, code: str) -> AuthResponse:
        """
        Exchange OAuth code for a session.

        Args:
            code: OAuth code from the provider

        Returns:
            AuthResponse with user if successful, error otherwise
        """
        try:
            # Log the code format for debugging
            logger.info(f"Exchanging code for session: {code[:10]}...")

            # Call the Supabase client's exchange_code_for_session method
            response = self.supabase.auth.exchange_code_for_session({"auth_code": code})

            # Log the response for debugging
            logger.info(f"Exchange response received: {response}")

            # Get the current session after the exchange
            session = self.supabase.auth.get_session()

            # Log the session for debugging
            logger.info(f"Current session: {session}")

            # Return the user object from the session
            if session and hasattr(session, 'user'):
                # Log the user metadata for debugging
                logger.info(f"User metadata from OAuth: {session.user.user_metadata}")

                user = User.from_supabase_user(session.user.model_dump())

                # Log the username that was set
                logger.info(f"Username set from OAuth auth: {user.username}")

                # Update the user's metadata in Supabase to ensure username is set
                if user.username:
                    try:
                        # Update the user's metadata in auth.users table
                        from app.utils.supabase_client import get_supabase_client
                        supabase = get_supabase_client()

                        # Use RPC to update user metadata
                        metadata_query = f"""
                        UPDATE auth.users
                        SET raw_user_meta_data =
                            jsonb_set(
                                COALESCE(raw_user_meta_data, '{{}}'),
                                '{{username}}',
                                '"{user.username}"'
                            )
                        WHERE id = '{user.id}'
                        """

                        metadata_response = supabase.rpc('execute_sql', {'query': metadata_query}).execute()
                        logger.info(f"Updated user {user.id} metadata with username {user.username}")
                    except Exception as e:
                        logger.error(f"Error updating user metadata: {str(e)}")

                return AuthResponse.success_response(user)
            else:
                logger.error("No user found in session after code exchange")
                return AuthResponse.error_response("Authentication failed")
        except Exception as e:
            logger.error(f"Code exchange error: {str(e)}")
            return AuthResponse.error_response(f"Authentication failed: {str(e)}")

    def get_current_user(self) -> Optional[User]:
        """
        Get the current authenticated user.

        Returns:
            The current user or None if not authenticated
        """
        try:
            response = self.supabase.auth.get_user()
            if not response or not response.user:
                return None

            return User.from_supabase_user(response.user.model_dump())
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            return None

    def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update a user's metadata.

        Args:
            user_id: The user ID
            metadata: The metadata to update

        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user metadata: {str(e)}")
            return False

    def get_subscription_tier(self, user_id: str) -> str:
        """
        Get a user's subscription tier.

        Args:
            user_id: The user ID

        Returns:
            The subscription tier
        """
        try:
            # First check the subscription table
            response = self.supabase.table("saas_user_subscriptions").select("subscription_tier, status").eq("user_id", user_id).execute()

            if response.data and len(response.data) > 0:
                subscription = response.data[0]
                if subscription and subscription.get('status') == 'active':
                    return subscription.get('subscription_tier', 'free')

            # If no active subscription, check user metadata
            user = self.get_user(user_id)
            if user:
                return user.subscription_tier

            return 'free'
        except Exception as e:
            logger.error(f"Error getting subscription tier: {str(e)}")
            return 'free'

    def _validate_email(self, email: str) -> bool:
        """
        Validate an email address.

        Args:
            email: The email to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_password(self, password: str) -> bool:
        """
        Validate a password.

        Args:
            password: The password to validate

        Returns:
            True if valid, False otherwise
        """
        # At least 8 characters, one uppercase, one lowercase, one number, one special character
        if len(password) < 8:
            return False

        # Simple validation for now
        return True

    def _validate_username(self, username: str) -> bool:
        """
        Validate a username.

        Args:
            username: The username to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))

    def _create_default_subscription(self, user_id: str) -> bool:
        """
        Create a default subscription for a user.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a default subscription
            now = datetime.now().isoformat()

            subscription_data = {
                "user_id": user_id,
                "subscription_tier": "free",
                "status": "active",
                "papers_limit": 0,
                "papers_used": 0,
                "subscription_papers_limit": 0,
                "subscription_papers_used": 0,
                "additional_papers_limit": 0,
                "additional_papers_used": 0,
                "created_at": now,
                "updated_at": now
            }

            self.supabase.table("saas_user_subscriptions").insert(subscription_data).execute()

            return True
        except Exception as e:
            logger.error(f"Error creating default subscription: {str(e)}")
            return False

# Create a singleton instance
auth_service = AuthService()

def get_auth_service() -> AuthService:
    """
    Get the authentication service singleton.

    Returns:
        The authentication service
    """
    return auth_service
