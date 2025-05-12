"""
Authentication routes for Lily AI.

This module provides authentication API routes.
"""

import logging
import os
from typing import Optional
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from auth.service import AuthService
from app.utils.session import get_session_manager

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["auth"])

# Get services
auth_service = AuthService()
session_manager = get_session_manager()

# Templates
templates = Jinja2Templates(directory="templates")

# Get reCAPTCHA keys from environment
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")

@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Render the registration page.

    Args:
        request: The incoming request

    Returns:
        The registration page HTML
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "recaptcha_site_key": RECAPTCHA_SITE_KEY
        }
    )

@router.post("/auth/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    name: Optional[str] = Form(None),
    g_recaptcha_response: Optional[str] = Form(None)
):
    """
    Register a new user.

    Args:
        request: The incoming request
        email: The user's email
        password: The user's password
        username: The user's username
        name: The user's name (optional)
        g_recaptcha_response: The reCAPTCHA response token

    Returns:
        Redirect to login page or registration page with error
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Verify reCAPTCHA
    from app.utils.recaptcha import verify_recaptcha_enterprise

    # Log the reCAPTCHA response for debugging
    if g_recaptcha_response:
        logger.info(f"reCAPTCHA response provided: {g_recaptcha_response[:20]}...")
    else:
        logger.warning("No reCAPTCHA response provided")

    # TEMPORARY: Skip reCAPTCHA verification completely
    logger.warning("TEMPORARY: Skipping reCAPTCHA verification completely")
    is_human = True

    if not is_human:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "reCAPTCHA verification failed. Please try again.",
                "email": email,
                "username": username,
                "name": name,
                "recaptcha_site_key": RECAPTCHA_SITE_KEY,
                "captcha_error": "reCAPTCHA verification failed. Please try again."
            }
        )

    # Register the user
    response = auth_service.sign_up(email, password, username, name)

    # Check if the response is a tuple (success, message) or an AuthResponse object
    if isinstance(response, tuple):
        is_success, message = response
        if is_success:
            # Redirect to login page with success message
            return RedirectResponse(
                url="/auth/login?registered=true",
                status_code=303
            )
        else:
            # Return to registration page with error
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": message,
                    "email": email,
                    "username": username,
                    "name": name,
                    "recaptcha_site_key": RECAPTCHA_SITE_KEY
                }
            )
    else:
        # Handle AuthResponse object
        if response.is_success:
            # Redirect to login page with success message
            return RedirectResponse(
                url="/auth/login?registered=true",
                status_code=303
            )
        else:
            # Return to registration page with error
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": response.error,
                    "email": email,
                    "username": username,
                    "name": name,
                    "recaptcha_site_key": RECAPTCHA_SITE_KEY
                }
            )

@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: bool = False, verified: bool = False, error: Optional[str] = None):
    """
    Render the login page.

    Args:
        request: The incoming request
        registered: Whether the user just registered
        verified: Whether the user just verified their email
        error: Error message to display

    Returns:
        The login page HTML
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "registered": registered,
            "verified": verified,
            "error": error
        }
    )

@router.post("/auth/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Log in a user.

    Args:
        request: The incoming request
        email: The user's email
        password: The user's password

    Returns:
        Redirect to dashboard or login page with error
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    try:
        # Log in the user
        response = auth_service.sign_in(email, password)

        # Check if the response is a tuple (success, message, user) or an AuthResponse object
        if isinstance(response, tuple):
            is_success, message, user = response if len(response) == 3 else (response[0], response[1], None)

            if is_success and user:
                # Set session data
                session_manager.set_session_user(request, user)

                # Redirect to dashboard
                return RedirectResponse(url="/dashboard", status_code=303)
            else:
                # Return to login page with error
                return templates.TemplateResponse(
                    "auth/login.html",
                    {
                        "request": request,
                        "error": message,
                        "email": email
                    }
                )
        else:
            # Handle AuthResponse object
            if response.is_success:
                # Set session data
                session_manager.set_session_user(request, response.user)

                # Redirect to dashboard
                return RedirectResponse(url="/dashboard", status_code=303)
            else:
                # Return to login page with error
                return templates.TemplateResponse(
                    "auth/login.html",
                    {
                        "request": request,
                        "error": response.error,
                        "email": email
                    }
                )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        # Return to login page with generic error
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "An error occurred during login. Please try again.",
                "email": email
            }
        )

@router.get("/auth/logout")
async def logout(request: Request):
    """
    Log out a user.

    Args:
        request: The incoming request

    Returns:
        Redirect to home page
    """
    # Sign out from Supabase
    auth_service.sign_out()

    # Clear session
    session_manager.clear_session(request)

    # Redirect to home page
    return RedirectResponse(url="/", status_code=303)

@router.get("/auth/oauth/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.

    Args:
        request: The incoming request

    Returns:
        Redirect to Google OAuth authorization endpoint
    """
    redirect_url = request.query_params.get("redirect_to", "/dashboard")
    oauth_url = auth_service.get_oauth_url("google", redirect_url)

    # Note: The prompt parameter is already added in auth_service.get_oauth_url
    logger.info(f"Initiating Google OAuth login flow with URL: {oauth_url}")
    return RedirectResponse(url=oauth_url, status_code=303)

@router.get("/auth/callback")
async def oauth_callback(request: Request):
    """
    Handle OAuth callback from provider (e.g., Google).

    Args:
        request: The incoming request with oauth code

    Returns:
        Redirect to dashboard or error page
    """
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")

    # Log all query parameters for debugging
    logger.info(f"OAuth callback received with params: {dict(request.query_params)}")

    if error or error_description:
        logger.error(f"OAuth error received: {error} - {error_description}")
        return RedirectResponse(
            url=f"/auth/login?error=Authentication+failed:+{error}",
            status_code=303
        )

    if not code:
        logger.error("OAuth callback missing code parameter")
        return RedirectResponse(
            url="/auth/login?error=Authentication+failed",
            status_code=303
        )

    try:
        logger.info(f"Exchanging OAuth code for session")
        # Exchange code for session
        user = auth_service.exchange_code_for_session(code)

        # Create a response object similar to what the set_session_user expects
        from auth.models import AuthResponse, User

        if not user:
            logger.error("Failed to exchange OAuth code for session")
            return RedirectResponse(
                url="/auth/login?error=Authentication+failed",
                status_code=303
            )

        # Convert the user object to our expected format
        response = AuthResponse(
            is_success=True,
            user=User(
                id=user.id,
                email=user.email,
                username=user.user_metadata.get("username", user.email.split('@')[0]) if user.user_metadata else user.email.split('@')[0],
                name=user.user_metadata.get("name", "") if user.user_metadata else "",
                subscription_tier=user.user_metadata.get("subscription_tier", "free") if user.user_metadata else "free",
                created_at=user.created_at,
                updated_at=user.updated_at
            ),
            message="Authentication successful"
        )

        # Set session data
        logger.info(f"Setting session data for user: {response.user.id}")
        session_manager.set_session_user(request, response.user)

        # Check if this is a new user (created_at and updated_at are close)
        is_new_user = False
        if user.created_at and user.updated_at:
            created_time = user.created_at
            updated_time = user.updated_at

            # Convert to datetime objects if they're strings
            if isinstance(created_time, str):
                from datetime import datetime
                created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
            if isinstance(updated_time, str):
                from datetime import datetime
                updated_time = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))

            # Check if the times are close (within 5 minutes)
            from datetime import timedelta
            is_new_user = abs((updated_time - created_time).total_seconds()) < 300

        # Send welcome email for new Google OAuth users
        if is_new_user:
            try:
                # Import notification service
                from app.services.notification.notification_service import NotificationService

                # Initialize notification service
                notification_service = NotificationService(auth_service.supabase)

                # Send the welcome email immediately (without background tasks)
                result = await notification_service.notify(
                    event_type="email.verified",
                    user_id=user.id,
                    data=None
                )

                if result.get('success'):
                    logger.info(f"Welcome email sent to new OAuth user: {user.email}")
                else:
                    logger.error(f"Failed to send welcome email to OAuth user: {result.get('message')}")
            except Exception as e:
                logger.error(f"Error sending welcome email to OAuth user: {str(e)}")
                # Continue with login even if welcome email fails

        # Redirect to next URL or dashboard
        next_url = request.query_params.get("next", "/dashboard")
        logger.info(f"User logged in via OAuth: {response.user.email}")
        return RedirectResponse(url=next_url, status_code=303)

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(
            url="/auth/login?error=Authentication+failed",
            status_code=303
        )

@router.get("/auth/v1/callback")
async def oauth_v1_callback(request: Request):
    """
    Handler for Supabase's /auth/v1/callback route.
    Redirects to our internal /auth/callback route.

    Args:
        request: The incoming request

    Returns:
        Redirect to our internal callback handler
    """
    # Preserve all query parameters
    query_string = request.url.query
    logger.info(f"Received OAuth request at /auth/v1/callback with params: {query_string}")

    # Redirect to our internal callback endpoint with all query parameters
    return RedirectResponse(
        url=f"/auth/callback?{query_string}",
        status_code=303
    )

@router.get("/auth/verify")
async def verify_email(request: Request, token: str):
    """
    Verify a user's email and automatically log the user in.

    Args:
        request: The incoming request
        token: The verification token

    Returns:
        Redirect to dashboard or login page with error
    """
    try:
        # Exchange the token for a session
        response = auth_service.supabase.auth.exchange_code_for_session({
            "auth_code": token
        })

        if response and response.user:
            logger.info(f"Email verification successful for user: {response.user.email}")

            # Set session data to automatically log the user in
            from auth.models import User
            user_data = User(
                id=response.user.id,
                email=response.user.email,
                username=response.user.user_metadata.get("username", response.user.email.split('@')[0]) if response.user.user_metadata else response.user.email.split('@')[0],
                name=response.user.user_metadata.get("name", "") if response.user.user_metadata else "",
                subscription_tier=response.user.user_metadata.get("subscription_tier", "free") if response.user.user_metadata else "free",
                created_at=response.user.created_at,
                updated_at=response.user.updated_at
            )

            # Set the user in the session
            session_manager.set_session_user(request, user_data)
            logger.info(f"User automatically logged in after email verification: {response.user.email}")

            # Redirect to dashboard with welcome message
            return RedirectResponse(
                url="/dashboard?verified=true",
                status_code=303
            )
        else:
            # Redirect to login page with error
            logger.error("Email verification failed: No user in response")
            return RedirectResponse(
                url="/auth/login?error=Email verification failed. Please try again or contact support.",
                status_code=303
            )
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")

        # Redirect to login page with error
        return RedirectResponse(
            url=f"/auth/login?error=Email verification failed: {str(e)}",
            status_code=303
        )
