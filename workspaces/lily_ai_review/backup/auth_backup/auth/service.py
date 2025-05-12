"""
Authentication service module.

This module provides services for handling authentication operations with Supabase.
"""
import os
from typing import Optional, Dict, Any
import logging
from .client import get_supabase_client
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Add a stream handler to output logs to console
import sys
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class AuthService:
    """
    Service for handling authentication operations with Supabase.
    Provides clean interfaces for user authentication, registration, and management.
    """
    def __init__(self):
        """Initialize the authentication service with Supabase client."""
        self.supabase = get_supabase_client()

    def sign_in(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's password

        Returns:
            User data if authentication is successful, None otherwise
        """
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.user if response.user else None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def sign_up(self, email: str, password: str, username: str, name: str = None) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user.

        Args:
            email: User's email address
            password: User's password
            username: User's username
            name: User's full name (optional)

        Returns:
            Tuple of (user data, error message). If registration is successful, error message is None.
            If registration fails, user data is None and error message contains the reason.
        """
        try:
            # Normalize inputs
            email = email.lower().strip()
            username = username.strip()

            logger.info(f"Starting registration process for email: {email}, username: {username}")

            # Check if email exists in auth.users
            try:
                auth_email_query = """
                SELECT COUNT(*) FROM auth.users WHERE LOWER(email) = LOWER($1)
                """
                auth_email_result = self.supabase.rpc('execute_sql', {
                    'query': auth_email_query,
                    'params': [email]
                }).execute()

                logger.info(f"auth_email_result: {auth_email_result.data}")

                if auth_email_result.data and auth_email_result.data[0]['count'] > 0:
                    logger.error(f"Email already exists in auth.users: {email}")
                    return None, "Email address is already registered. Please use a different email or sign in."
            except Exception as check_error:
                logger.error(f"Error checking auth.users: {str(check_error)}")

            # Check if username exists in auth.users metadata
            try:
                username_query = """
                SELECT COUNT(*) FROM auth.users
                WHERE raw_user_meta_data->>'username' = $1
                """
                username_result = self.supabase.rpc('execute_sql', {
                    'query': username_query,
                    'params': [username]
                }).execute()

                logger.info(f"username_result: {username_result.data}")

                if username_result.data and username_result.data[0]['count'] > 0:
                    logger.error(f"Username already exists in auth.users metadata: {username}")
                    return None, "Username is already taken. Please choose a different username."
            except Exception as check_error:
                logger.error(f"Error checking auth.users for username: {str(check_error)}")

            # Set up user metadata
            user_metadata = {
                "username": username,
                "name": name if name else username,
                "subscription_tier": "free"
            }

            # Register the user with Supabase Auth
            try:
                logger.info(f"Attempting to register user with Supabase Auth: {email}")

                # Direct sign-up with Supabase
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": user_metadata
                    }
                })

                if not response.user:
                    logger.error(f"User registration failed: {email}, no user in response")
                    if hasattr(response, 'error'):
                        logger.error(f"Error details: {response.error}")
                        return None, f"Registration failed: {response.error}"
                    return None, "Registration failed. Please try again later."

                logger.info(f"User registration successful: {email}, user_id: {response.user.id}")

                # Create a default subscription in saas_user_subscriptions table
                try:
                    # Convert datetime objects to ISO format strings for JSON serialization
                    created_at = response.user.created_at
                    if hasattr(created_at, 'isoformat'):
                        created_at = created_at.isoformat()

                    # Create a default subscription
                    subscription_data = {
                        'user_id': response.user.id,
                        'subscription_tier': 'free',
                        'status': 'active',
                        'papers_limit': 0,  # Will be set by subscription service defaults
                        'papers_used': 0,
                        'created_at': created_at,
                        'updated_at': created_at
                    }

                    subscription_response = self.supabase.table('saas_user_subscriptions').insert(subscription_data).execute()

                    if not subscription_response.data or len(subscription_response.data) == 0:
                        logger.warning(f"Failed to create subscription for user: {email}, but continuing with registration")
                    else:
                        logger.info(f"Default subscription created for user: {email}")

                    return response.user, None

                except Exception as sub_error:
                    logger.warning(f"Error creating subscription for user: {str(sub_error)}, but continuing with registration")
                    return response.user, None

            except Exception as auth_error:
                logger.error(f"Error creating user in auth.users: {str(auth_error)}")
                if hasattr(auth_error, 'message'):
                    logger.error(f"Error message: {auth_error.message}")

                # Check for common error messages
                error_msg = str(auth_error)
                if "User already registered" in error_msg:
                    return None, "Email address is already registered. Please use a different email or sign in."
                elif "Password should be at least" in error_msg:
                    return None, "Password is too short. Please use a longer password."
                elif "Invalid email" in error_msg:
                    return None, "Invalid email format. Please enter a valid email address."

                return None, "Registration failed. Please try again later."

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            # Try to get more detailed error information
            if hasattr(e, 'to_dict'):
                logger.error(f"Error details: {e.to_dict()}")
            elif hasattr(e, 'response') and hasattr(e.response, 'json'):
                try:
                    logger.error(f"Response JSON: {e.response.json()}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            return None, "Registration failed. Please try again later."

    def get_oauth_url(self, provider: str, redirect_url: str = None) -> str:
        """
        Get OAuth URL for the specified provider.

        Args:
            provider: The OAuth provider (e.g., 'google', 'facebook')
            redirect_url: URL to redirect to after authentication

        Returns:
            OAuth URL for redirection

        Raises:
            Exception: If OAuth URL generation fails
        """
        try:
            options = {}

            # Special handling for Google OAuth
            if provider.lower() == 'google':
                # Explicitly set redirectTo to match the URL configured in Supabase
                # This ensures the redirect URL is consistent
                import os
                import socket

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

    def exchange_code_for_session(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange OAuth code for a session.

        Args:
            code: OAuth code from the provider

        Returns:
            User data if exchange is successful, None otherwise

        Raises:
            Exception: If code exchange fails
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
                else:
                    logger.error("Session has no user attribute")
            else:
                logger.error("No session returned from get_session()")

            # Return the user object from the session
            if session and hasattr(session, 'user'):
                return session.user
            else:
                logger.error("No user found in session after code exchange")
                return None
        except Exception as e:
            logger.error(f"Code exchange error: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception args: {e.args}")
            # Try to get more detailed error information
            if hasattr(e, 'to_dict'):
                logger.error(f"Error details: {e.to_dict()}")
            raise

    def sign_out(self, token: str = None) -> bool:
        """
        Sign out a user.

        Args:
            token: User's JWT token (optional)

        Returns:
            True if sign out is successful, False otherwise
        """
        try:
            # The sign_out method doesn't accept a jwt parameter
            self.supabase.auth.sign_out()

            # Log the sign-out attempt
            logger.info("User signed out successfully from Supabase")

            # Clear any local session data
            try:
                # Get the current session and invalidate it if it exists
                session = self.supabase.auth.get_session()
                if session and hasattr(session, 'access_token'):
                    logger.info("Found active session, attempting to invalidate it")
                    # No direct method to invalidate a session in Supabase JS client
                    # The sign_out above should handle this
            except Exception as session_error:
                logger.error(f"Error clearing session: {str(session_error)}")

            return True
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by ID.

        Args:
            user_id: The user's ID

        Returns:
            User data if found, None otherwise
        """
        try:
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            return response.user if response.user else None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None

    def get_subscription_tier(self, user_id: str) -> str:
        """
        Get the subscription tier from auth.users metadata.

        Args:
            user_id: The user's ID

        Returns:
            Subscription tier (free, premium, etc.) or 'free' if not found
        """
        try:
            # First, check if there's a subscription in saas_user_subscriptions
            response = self.supabase.table('saas_user_subscriptions').select('subscription_tier').eq('user_id', user_id).eq('status', 'active').execute()

            if response.data and len(response.data) > 0:
                # Log the subscription tier for debugging
                tier = response.data[0]['subscription_tier']
                logger.info(f"Found subscription tier in saas_user_subscriptions table: {tier} for user {user_id}")
                return tier

            # If not found in subscriptions, get from auth.users metadata
            user = self.get_user(user_id)
            if user and user.user_metadata:
                tier = user.user_metadata.get('subscription_tier', 'free')
                logger.info(f"Using subscription tier from user metadata: {tier} for user {user_id}")
                return tier

            logger.info(f"No subscription tier found, defaulting to 'free' for user {user_id}")
            return 'free'
        except Exception as e:
            logger.error(f"Error getting subscription tier: {str(e)}")
            return 'free'

    def verify_password(self, user_id: str, password: str) -> bool:
        """
        Verify a user's password.

        Args:
            user_id: The user's ID
            password: The password to verify

        Returns:
            True if password is correct, False otherwise
        """
        try:
            # Get the user's email
            user = self.get_user(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            # Try to sign in with the email and password
            result = self.sign_in(user.email, password)

            # If sign in succeeds, the password is correct
            return result is not None
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False

    def update_password(self, user_id: str, new_password: str) -> bool:
        """
        Update a user's password.

        Args:
            user_id: The user's ID
            new_password: The new password

        Returns:
            True if update is successful, False otherwise
        """
        try:
            # Update the user's password
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"password": new_password}
            )
            logger.info(f"Password updated for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            return False

    def update_email(self, user_id: str, new_email: str) -> bool:
        """
        Update a user's email address.

        Args:
            user_id: The user's ID
            new_email: The new email address

        Returns:
            True if update is successful, False otherwise
        """
        try:
            # Update the user's email
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {
                    "email": new_email,
                    "email_confirm": False  # Require email verification
                }
            )
            logger.info(f"Email update initiated for user: {user_id} to {new_email}")
            return True
        except Exception as e:
            logger.error(f"Error updating email: {str(e)}")
            return False
