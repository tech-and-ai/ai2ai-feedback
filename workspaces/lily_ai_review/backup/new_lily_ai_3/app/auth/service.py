"""
Authentication service for Lily AI.

This module provides authentication functionality.
"""

import os
import re
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

from app.database import get_db_client
from app.auth.models import User, AuthResponse

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
        self.db_client = get_db_client()
        self.supabase = self.db_client.client

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
            existing_user = self.db_client.get_user_by_username(username)
            if existing_user:
                return AuthResponse.error_response("Username is already taken")

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

    def sign_in_with_google(self) -> str:
        """
        Get the Google OAuth sign-in URL.

        Returns:
            The Google OAuth sign-in URL
        """
        try:
            # Get the redirect URL
            redirect_url = os.getenv("APP_URL", "http://localhost:8004") + "/auth/callback"

            # Get the Google OAuth sign-in URL
            response = self.supabase.auth.sign_in_with_oauth({
                "provider": "google",
                "options": {
                    "redirect_to": redirect_url
                }
            })

            # Return the URL
            return response.url
        except Exception as e:
            logger.error(f"Error getting Google sign-in URL: {str(e)}")
            raise

    def exchange_code_for_session(self, code: str) -> AuthResponse:
        """
        Exchange an OAuth code for a session.

        Args:
            code: The OAuth code

        Returns:
            An AuthResponse instance
        """
        try:
            # Exchange the code for a session
            response = self.supabase.auth.exchange_code_for_session({"auth_code": code})

            if not response or not response.user:
                return AuthResponse.error_response("Failed to authenticate with Google")

            # Check if this is a new user
            is_new_user = response.user.app_metadata.get("provider") == "google" and \
                          response.user.created_at == response.user.updated_at

            # If this is a new user, set up their account
            if is_new_user:
                # Extract username from email
                email = response.user.email
                username = email.split('@')[0]

                # Check if username exists
                existing_user = self.db_client.get_user_by_username(username)
                if existing_user:
                    # Append random numbers to make it unique
                    import random
                    username = f"{username}{random.randint(1000, 9999)}"

                # Update user metadata
                self.db_client.update_user_metadata(response.user.id, {
                    "username": username,
                    "name": response.user.user_metadata.get("full_name", username),
                    "subscription_tier": "free"
                })

                # Create a default subscription
                self._create_default_subscription(response.user.id)

            # Create User model from response
            user = User.from_supabase_user(response.user.model_dump())

            return AuthResponse.success_response(user)
        except Exception as e:
            logger.error(f"Error exchanging code for session: {str(e)}")
            return AuthResponse.error_response(f"An error occurred during authentication: {str(e)}")

    def get_oauth_url(self, provider: str, redirect_url: Optional[str] = None) -> str:
        """
        Get the OAuth URL for a provider.

        Args:
            provider: The OAuth provider (e.g., 'google')
            redirect_url: The URL to redirect to after authentication

        Returns:
            The OAuth URL
        """
        try:
            # Set up options
            options = {}

            # Special handling for Google OAuth
            if provider.lower() == 'google':
                # Get the base URL
                base_url = os.getenv("APP_URL", "http://localhost:8004")

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
                logger.info(f"Using minimal scopes: {options['scopes']}")

                # Add query parameters to force account selection and consent screen
                options["queryParams"] = {
                    "prompt": "select_account consent",  # Force account selection and consent screen
                    "access_type": "online"              # Standard access type
                }
                logger.info(f"Added queryParams to force account selection and consent screen")

                # Log the complete options for debugging
                logger.info(f"Complete options for Google OAuth: {options}")
            elif redirect_url:
                options["redirectTo"] = f"{redirect_url}"
                logger.info(f"Non-Google OAuth redirectTo set to: {redirect_url}")

            response = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": options
            })

            # Get the base URL from the response
            oauth_url = response.url

            # For Google OAuth, manually add the prompt parameter to force account selection
            if provider.lower() == 'google':
                # Add prompt=select_account+consent to force account selection and consent screen
                if '?' in oauth_url:
                    oauth_url += '&prompt=select_account+consent&access_type=online'
                else:
                    oauth_url += '?prompt=select_account+consent&access_type=online'
                logger.info(f"Added prompt=select_account+consent to OAuth URL")

            logger.info(f"Generated OAuth URL for {provider}: {oauth_url}")
            return oauth_url
        except Exception as e:
            logger.error(f"OAuth URL generation error: {str(e)}")
            raise

    def exchange_code_for_session(self, code: str) -> Optional[User]:
        """
        Exchange an OAuth code for a session.

        Args:
            code: The OAuth code

        Returns:
            The user if successful, None otherwise
        """
        try:
            # Log the code format for debugging
            logger.info(f"Exchanging code for session: {code[:10]}...")

            # Call the Supabase client's exchange_code_for_session method with the correct format
            # The method expects a dictionary with 'auth_code' key, not a string
            response = self.supabase.auth.exchange_code_for_session({"auth_code": code})

            # Log the response for debugging
            logger.info(f"Exchange response received: {response}")

            # Get the current session after the exchange
            session = self.supabase.auth.get_session()

            # Log the session for debugging
            logger.info(f"Current session: {session}")

            # Log session details for debugging
            if session:
                logger.info(f"Session access token: {session.access_token[:20]}...")
                logger.info(f"Session refresh token: {session.refresh_token[:20]}...")
                logger.info(f"Session expires at: {session.expires_at}")

                # Log user details
                if hasattr(session, 'user'):
                    logger.info(f"User ID: {session.user.id}")
                    logger.info(f"User email: {session.user.email}")
                    logger.info(f"User metadata: {session.user.user_metadata}")
                    logger.info(f"User app metadata: {session.user.app_metadata}")

                    # Check if this is a new user
                    is_new_user = session.user.app_metadata.get("provider") == "google" and \
                                session.user.created_at == session.user.updated_at

                    # If this is a new user, set up their account
                    if is_new_user:
                        logger.info(f"New user via OAuth: {session.user.email}")

                        # Extract username from email
                        email = session.user.email
                        username = email.split('@')[0]

                        # Check if username exists
                        existing_user = self.db_client.get_user_by_username(username)
                        if existing_user:
                            # Append random numbers to make it unique
                            import random
                            username = f"{username}{random.randint(1000, 9999)}"

                        # Update user metadata
                        self.db_client.update_user_metadata(session.user.id, {
                            "username": username,
                            "name": session.user.user_metadata.get("full_name", username),
                            "subscription_tier": "free"
                        })

                        # Create a default subscription
                        self._create_default_subscription(session.user.id)

                    # Create User model from session
                    user = User.from_supabase_user(session.user.model_dump())
                    return user
                else:
                    logger.error("Session has no user attribute")
            else:
                logger.error("No session returned from get_session()")

            return None
        except Exception as e:
            logger.error(f"Error exchanging code for session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

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
            # First try to get the current user from the session
            # This is more reliable than querying the database
            current_user = self.get_current_user()
            if current_user and current_user.id == user_id:
                return current_user

            # If that fails, try to get the user from the admin API
            # This requires admin privileges and may not work
            try:
                user_data = self.db_client.get_user_by_id(user_id)
                if user_data:
                    return User.from_supabase_user(user_data)
            except Exception as e:
                logger.warning(f"Could not get user from database: {str(e)}")

            # If all else fails, return None
            return None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

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
        return self.db_client.update_user_metadata(user_id, metadata)

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
            subscription = self.db_client.get_subscription(user_id)
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

    def resend_verification_email(self, email: str) -> bool:
        """
        Resend verification email to a user.

        Args:
            email: The user's email

        Returns:
            True if successful, False otherwise
        """
        try:
            # Resend verification email via Supabase
            self.supabase.auth.resend_signup_email({"email": email})
            logger.info(f"Verification email resent to: {email}")
            return True
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            return False

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
            query = """
            INSERT INTO lily_subscriptions (
                user_id,
                subscription_tier,
                status,
                papers_limit,
                papers_used,
                created_at,
                updated_at
            ) VALUES (
                $1, 'free', 'active', 0, 0, $2, $2
            )
            """

            now = datetime.now().isoformat()
            self.db_client.execute_query(query, [user_id, now])

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
