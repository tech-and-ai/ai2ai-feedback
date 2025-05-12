"""
Authentication middleware module.

This module provides middleware for handling authentication in FastAPI applications.
"""
from fastapi import Request, status
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.templating import Jinja2Templates
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="templates")

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling authentication.
    Protects routes that require authentication and redirects unauthenticated users.
    """
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and enforce authentication for protected routes.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the next handler or a redirect/error response
        """
        # Log session contents for debugging
        logger.info(f"Session contents: {dict(request.session)}")

        # Ensure username is set if user_id is present but username is not
        if "user_id" in request.session and (not request.session.get("username") or request.session.get("username") == "None"):
            try:
                # Get user data from Supabase
                from app.utils.supabase_client import get_supabase_client
                supabase = get_supabase_client()

                user_id = request.session.get("user_id")
                email = request.session.get("email")

                # Use RPC to get user data
                user_query = f"""
                SELECT * FROM auth.users WHERE id = '{user_id}'
                """

                user_response = supabase.rpc('execute_sql', {'query': user_query}).execute()

                # Default username to email prefix if nothing else works
                username = email.split('@')[0] if email else None

                if user_response and user_response.data and len(user_response.data) > 0:
                    user_data = user_response.data[0]
                    user_metadata = user_data.get('raw_user_meta_data', {}) or {}

                    # Get username from metadata
                    metadata_username = user_metadata.get('username')
                    name = user_metadata.get('name')

                    # If we have a username in metadata, use it
                    if metadata_username:
                        username = metadata_username
                    # If no username but we have a name, create a username from the name
                    elif name:
                        username = name.lower().replace(' ', '_')

                # Update session with username
                if username:
                    request.session["username"] = username
                    logger.info(f"Updated session with username: {username}")

                    # Update user metadata in Supabase if needed
                    try:
                        metadata_query = f"""
                        UPDATE auth.users
                        SET raw_user_meta_data =
                            jsonb_set(
                                COALESCE(raw_user_meta_data, '{{}}'),
                                '{{username}}',
                                '"{username}"'
                            )
                        WHERE id = '{user_id}'
                        """

                        supabase.rpc('execute_sql', {'query': metadata_query}).execute()
                        logger.info(f"Updated user {user_id} metadata with username {username}")
                    except Exception as metadata_error:
                        logger.error(f"Error updating user metadata: {str(metadata_error)}")
            except Exception as e:
                logger.error(f"Error ensuring username is set: {str(e)}")
                # If all else fails, set username to email prefix
                if "email" in request.session and not request.session.get("username"):
                    email = request.session.get("email")
                    if email:
                        username = email.split('@')[0]
                        request.session["username"] = username
                        logger.info(f"Set fallback username from email: {username}")

        # Special handling for profile and account pages - always require authentication
        if request.url.path == "/profile" or request.url.path == "/account/manage":
            if "user_id" not in request.session:
                logger.warning(f"Unauthenticated access attempt to protected page: {request.url.path}")
                return RedirectResponse(
                    url=f"/auth/login?next={request.url.path}&message=Please log in to access this page",
                    status_code=status.HTTP_303_SEE_OTHER
                )
            else:
                logger.info(f"User authenticated: {request.session.get('user_id')} - {request.session.get('email')}")
                return await call_next(request)

        # Check if user is authenticated via session
        if "user_id" in request.session:
            # User is authenticated, proceed
            logger.info(f"User authenticated: {request.session.get('user_id')} - {request.session.get('email')}")
            return await call_next(request)

        # User is not authenticated
        # Allow access to public routes
        if self._is_public_route(request.url.path):
            logger.info(f"Public route access: {request.url.path}")
            return await call_next(request)

        # For protected routes, show 401 page or return JSON response for API
        if request.url.path.startswith("/api/"):
            logger.warning(f"Unauthenticated API access attempt: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"}
            )
        elif request.url.path.startswith("/billing/checkout/"):
            # For checkout routes, redirect to login with a message
            logger.warning(f"Unauthenticated access attempt to protected page: {request.url.path}")
            return RedirectResponse(
                url=f"/auth/login?next={request.url.path}&message=Please log in to access this page",
                status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            # Render the 401 error page with a link to login
            logger.warning(f"Unauthorized access attempt: {request.url.path}")
            return templates.TemplateResponse(
                "errors/401.html",
                {"request": request},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

    def _is_public_route(self, path: str) -> bool:
        """
        Check if a route is public (doesn't require authentication).

        Args:
            path: The request path

        Returns:
            True if the route is public, False otherwise
        """
        # Special case for /profile and /account/manage - these are never public
        if path == "/profile" or path == "/account/manage":
            return False

        public_prefixes = [
            "/static/",
            "/auth/login",
            "/auth/register",
            "/auth/reset-password",
            "/auth/verify-email",     # Email verification page
            "/auth/verify",           # Email verification callback
            "/auth/verify-success",   # Email verification success page
            "/auth/resend-verification", # Resend verification email
            "/auth/reset-confirmation", # Password reset confirmation
            "/auth/oauth/google",     # Google OAuth route
            "/auth/callback",         # OAuth callback route
            "/",                      # Homepage
            "/about",
            "/pricing",
            "/contact",
            "/test-profile",          # Test route
            "/billing/webhook"        # Stripe webhook endpoint - must be public
        ]

        return any(path.startswith(prefix) for prefix in public_prefixes)
