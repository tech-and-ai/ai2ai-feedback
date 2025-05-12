"""
Authentication service for handling user signup, login, and verification.
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.config import config
from app.logging import get_logger
from .client import get_supabase_client
from app.services.email.email_service import EmailService

# Get logger
logger = get_logger(__name__)

class AuthService:
    """Service for handling authentication operations."""

    def __init__(self):
        """Initialize the authentication service."""
        self.supabase = get_supabase_client()
        self.email_service = EmailService()

    def sign_up(self, email: str, password: str, username: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user with email and password.

        Args:
            email: User's email address
            password: User's password
            username: User's username

        Returns:
            Tuple of (user data, error message)
        """
        try:
            # Normalize inputs
            email = email.lower().strip()
            username = username.strip()

            logger.info(f"Starting registration for email: {email}, username: {username}")

            # Check if email exists
            try:
                email_query = "SELECT COUNT(*) FROM auth.users WHERE LOWER(email) = LOWER($1)"
                email_result = self.supabase.rpc('execute_sql', {
                    'query': email_query,
                    'params': [email]
                }).execute()

                if email_result.data and email_result.data[0]['count'] > 0:
                    return None, "Email address is already registered"
            except Exception as e:
                logger.error(f"Error checking email: {str(e)}")

            # Check if username exists
            try:
                username_query = "SELECT COUNT(*) FROM auth.users WHERE raw_user_meta_data->>'username' = $1"
                username_result = self.supabase.rpc('execute_sql', {
                    'query': username_query,
                    'params': [username]
                }).execute()

                if username_result.data and username_result.data[0]['count'] > 0:
                    return None, "Username is already taken"
            except Exception as e:
                logger.error(f"Error checking username: {str(e)}")

            # Set up user metadata
            user_metadata = {
                "username": username,
                "subscription_tier": "free"
            }

            # Get the base URL from configuration (always researchassistant.uk)
            base_url = config.BASE_URL
            logger.info(f"Using base URL for email verification: {base_url}")

            # Register the user with email verification required
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata,
                    "email_redirect_to": f"{base_url}/auth/verify"
                }
            })

            # Log the response for debugging
            logger.info(f"Sign up response: {response}")

            if not response.user:
                return None, "Registration failed"

            # Create default subscription
            try:
                subscription_data = {
                    'user_id': response.user.id,
                    'subscription_tier': 'free',
                    'status': 'active',
                    'papers_limit': 1,
                    'papers_used': 0,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }

                self.supabase.table('saas_user_subscriptions').insert(subscription_data).execute()
                logger.info(f"Created default subscription for user: {email}")

                # Send welcome email
                try:
                    self.email_service.send_welcome_email(email)
                    logger.info(f"Welcome email sent to: {email}")
                except Exception as e:
                    logger.warning(f"Error sending welcome email: {str(e)}")
            except Exception as e:
                logger.warning(f"Error creating subscription: {str(e)}")

            return response.user, None

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return None, f"Registration failed: {str(e)}"

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

    def get_oauth_url(self, provider: str) -> str:
        """
        Get OAuth URL for the specified provider.

        Args:
            provider: The OAuth provider (e.g., 'google')

        Returns:
            OAuth URL for redirection
        """
        try:
            options = {}

            # Set redirect URL using configuration (always researchassistant.uk)
            base_url = config.BASE_URL
            callback_url = f"{base_url}/auth/callback"
            options["redirectTo"] = callback_url

            # Log the callback URL for debugging
            logger.info(f"Setting OAuth callback URL to: {callback_url}")

            # For Google, add specific options
            if provider.lower() == 'google':
                options["scopes"] = "openid email profile"
                # Force account selection and consent screen
                options["queryParams"] = {
                    "prompt": "select_account consent",
                    "access_type": "online"
                }

                # Log the query parameters for debugging
                logger.info(f"Setting Google OAuth query parameters: {options['queryParams']}")

                # Get the response with the OAuth URL
                response = self.supabase.auth.sign_in_with_oauth({
                    "provider": provider,
                    "options": options
                })

                # Get the base URL from the response
                oauth_url = response.url

                # Manually add the prompt parameter to force account selection
                # This is a workaround because some OAuth providers ignore the queryParams
                if '?' in oauth_url:
                    # Make sure we're not adding duplicate parameters
                    if 'prompt=' not in oauth_url:
                        oauth_url += '&prompt=select_account'
                    if 'access_type=' not in oauth_url:
                        oauth_url += '&access_type=online'
                else:
                    oauth_url += '?prompt=select_account&access_type=online'

                logger.info(f"Modified OAuth URL for Google: {oauth_url}")
                return oauth_url

            response = self.supabase.auth.sign_in_with_oauth({
                "provider": provider,
                "options": options
            })

            return response.url
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
        """
        try:
            # Exchange code for session (response not used directly)
            _ = self.supabase.auth.exchange_code_for_session({"auth_code": code})
            session = self.supabase.auth.get_session()

            if session and hasattr(session, 'user'):
                # Check if this is a new user (first login)
                is_new_user = False
                if hasattr(session.user, 'app_metadata') and session.user.app_metadata:
                    provider = session.user.app_metadata.get("provider")
                    if provider and provider != "email":
                        # Check if created_at and last_sign_in_at are close (within 5 seconds)
                        created_at = session.user.created_at
                        last_sign_in_at = session.user.last_sign_in_at
                        if abs((created_at - last_sign_in_at).total_seconds()) < 5:
                            is_new_user = True

                # For new OAuth users, create subscription and send welcome email
                if is_new_user:
                    try:
                        # Create default subscription
                        subscription_data = {
                            'user_id': session.user.id,
                            'subscription_tier': 'free',
                            'status': 'active',
                            'papers_limit': 1,
                            'papers_used': 0,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }

                        self.supabase.table('saas_user_subscriptions').insert(subscription_data).execute()
                        logger.info(f"Created default subscription for OAuth user: {session.user.email}")

                        # Send welcome email for OAuth users
                        self.email_service.send_welcome_email(session.user.email, is_oauth=True)
                    except Exception as e:
                        logger.warning(f"Error setting up new OAuth user: {str(e)}")

                return session.user
            else:
                logger.error("No user found in session after code exchange")
                return None
        except Exception as e:
            logger.error(f"Code exchange error: {str(e)}")
            raise

    def sign_out(self) -> bool:
        """
        Sign out a user.

        Returns:
            True if sign out is successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email.

        Args:
            email: The user's email

        Returns:
            User object if found, None otherwise
        """
        try:
            # Query the auth.users table
            response = self.supabase.table("auth.users").select("*").eq("email", email).execute()

            # Check if user exists
            if response.data and len(response.data) > 0:
                return response.data[0]

            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    def resend_verification_email(self, email: str) -> bool:
        """
        Resend verification email to a user.

        Args:
            email: The user's email

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the Supabase API to resend verification email
            self.supabase.auth.resend_signup_confirmation_email(email)
            logger.info(f"Verification email resent to: {email}")
            return True
        except Exception as e:
            logger.error(f"Error resending verification email: {str(e)}")
            return False
