"""
Main application file for Lily AI.

This file creates and configures the FastAPI application.
"""

import os
import logging
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import app modules
from app.auth import get_auth_service
from app.utils import get_session_manager, get_recaptcha_verifier
from app.database import get_db_client
from app.database.schema import create_schema, check_schema

# Create FastAPI app
app = FastAPI(title="Lily AI", description="Research Assistant powered by AI")

# Set up middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
secret_key = os.getenv("SESSION_SECRET_KEY", "supersecretkey")
app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="lily_session",
    max_age=86400,  # 1 day
    same_site="lax",
    https_only=False,  # Set to True in production
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Get services
auth_service = get_auth_service()
session_manager = get_session_manager()
db_client = get_db_client()
recaptcha_verifier = get_recaptcha_verifier()

# Check and create database schema if needed
@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting Lily AI application")

    # Check database schema
    schema_status = check_schema()
    all_exist = all(schema_status.values())

    if not all_exist:
        logger.info("Creating database schema")
        success = create_schema()
        if success:
            logger.info("Database schema created successfully")
        else:
            logger.error("Failed to create database schema")

# Define routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, code: str = None):
    """
    Home page.

    Args:
        request: The incoming request
        code: OAuth code (optional)

    Returns:
        The home page HTML or redirect to callback
    """
    # Check if this is an OAuth callback
    if code:
        logger.info(f"Detected OAuth code in root URL, redirecting to callback: {code[:10]}...")
        # Preserve all query parameters
        query_string = request.url.query
        return RedirectResponse(
            url=f"/auth/callback?{query_string}",
            status_code=303
        )

    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )

@app.get("/register", response_class=HTMLResponse)
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
            "recaptcha_site_key": recaptcha_verifier.get_site_key()
        }
    )

@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...),
    name: str = Form(None),
    g_recaptcha_response: str = Form(None)
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
    if recaptcha_verifier.site_key:
        # Get client IP
        client_ip = request.client.host if request.client else None

        # Verify reCAPTCHA token
        recaptcha_result = recaptcha_verifier.verify(
            token=g_recaptcha_response,
            action="register",
            remote_ip=client_ip
        )

        # Check if verification failed
        if not recaptcha_result.get("success", False):
            logger.warning(f"reCAPTCHA verification failed: {recaptcha_result}")
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": "reCAPTCHA verification failed. Please try again.",
                    "email": email,
                    "username": username,
                    "name": name,
                    "recaptcha_site_key": recaptcha_verifier.get_site_key()
                }
            )

        # Check score if available
        score = recaptcha_result.get("score", 0)
        if score < 0.5:
            logger.warning(f"reCAPTCHA score too low: {score}")
            return templates.TemplateResponse(
                "auth/register.html",
                {
                    "request": request,
                    "error": "Security check failed. Please try again.",
                    "email": email,
                    "username": username,
                    "name": name,
                    "recaptcha_site_key": recaptcha_verifier.get_site_key()
                }
            )

    # Register the user
    response = auth_service.sign_up(email, password, username, name)

    if response.is_success:
        # Store email in session for verification page
        request.session["pending_verification_email"] = email

        # Redirect to verification page
        return RedirectResponse(
            url="/verify-email",
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
                "recaptcha_site_key": recaptcha_verifier.get_site_key()
            }
        )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, registered: bool = False, verified: bool = False):
    """
    Render the login page.

    Args:
        request: The incoming request
        registered: Whether the user just registered
        verified: Whether the user just verified their email

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
            "recaptcha_site_key": recaptcha_verifier.get_site_key()
        }
    )

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    g_recaptcha_response: str = Form(None)
):
    """
    Log in a user.

    Args:
        request: The incoming request
        email: The user's email
        password: The user's password
        g_recaptcha_response: The reCAPTCHA response token

    Returns:
        Redirect to dashboard or login page with error
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Verify reCAPTCHA
    if recaptcha_verifier.site_key:
        # Get client IP
        client_ip = request.client.host if request.client else None

        # Verify reCAPTCHA token
        recaptcha_result = recaptcha_verifier.verify(
            token=g_recaptcha_response,
            action="login",
            remote_ip=client_ip
        )

        # Check if verification failed
        if not recaptcha_result.get("success", False):
            logger.warning(f"reCAPTCHA verification failed: {recaptcha_result}")
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Security check failed. Please try again.",
                    "email": email,
                    "recaptcha_site_key": recaptcha_verifier.get_site_key()
                }
            )

        # Check score if available
        score = recaptcha_result.get("score", 0)
        if score < 0.5:
            logger.warning(f"reCAPTCHA score too low: {score}")
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Security check failed. Please try again.",
                    "email": email,
                    "recaptcha_site_key": recaptcha_verifier.get_site_key()
                }
            )

    # Log in the user
    response = auth_service.sign_in(email, password)

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
                "email": email,
                "recaptcha_site_key": recaptcha_verifier.get_site_key()
            }
        )

@app.get("/logout")
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

@app.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, error: str = None):
    """
    Render the email verification page.

    Args:
        request: The incoming request
        error: Error message to display

    Returns:
        The verification page HTML
    """
    # Check if user is already logged in
    if session_manager.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Get email from session if available
    email = request.session.get("pending_verification_email", "")

    return templates.TemplateResponse(
        "auth/verify_email.html",
        {
            "request": request,
            "email": email,
            "error": error
        }
    )

@app.get("/verify", response_class=HTMLResponse)
async def verify_email(request: Request, token: str = None, type: str = None, error_description: str = None):
    """
    Handle email verification callback from Supabase.
    This is the endpoint that users are directed to when they click the verification link in their email.

    Args:
        request: The incoming request
        token: Verification token
        type: Type of verification (e.g., 'signup', 'recovery')
        error_description: Error description if verification failed

    Returns:
        Redirect to verification success page or error page
    """
    # Log the verification request
    logger.info(f"Email verification callback received with token: {token[:10] if token and len(token) > 10 else 'None'}... and type: {type}")

    if error_description:
        logger.error(f"Email verification error: {error_description}")
        return RedirectResponse(
            url=f"/login?error={error_description}",
            status_code=303
        )

    if not token or not type:
        logger.error("Missing token or type in verification callback")
        return RedirectResponse(
            url="/login?error=Invalid+verification+link",
            status_code=303
        )

    try:
        # This is a Supabase-generated link that we need to redirect to our welcome page
        # The actual verification is handled by Supabase when the user clicks the link
        logger.info(f"Email verification callback received with token: {token[:10]}... and type: {type}")

        # Redirect to the welcome page - we'll implement welcome emails in a future update
        logger.info("Email verified, redirecting to welcome page")

        # Redirect to the welcome page
        return RedirectResponse(
            url="/welcome",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        return RedirectResponse(
            url=f"/login?error=Error+verifying+email:+{str(e)}",
            status_code=303
        )

@app.get("/verify-success", response_class=HTMLResponse)
async def verify_success_page(request: Request):
    """
    Render the verification success page.

    Args:
        request: The incoming request

    Returns:
        The verification success page HTML
    """
    return templates.TemplateResponse(
        "auth/verify_success.html",
        {
            "request": request
        }
    )

@app.get("/welcome", response_class=HTMLResponse)
async def welcome_page(request: Request):
    """
    Render the welcome page after email verification.

    Args:
        request: The incoming request

    Returns:
        The welcome page HTML
    """
    return templates.TemplateResponse(
        "auth/welcome.html",
        {
            "request": request
        }
    )

@app.get("/resend-verification", response_class=HTMLResponse)
async def resend_verification(request: Request):
    """
    Resend verification email.

    Args:
        request: The incoming request

    Returns:
        Redirect back to verification page
    """
    email = request.session.get("pending_verification_email")

    if not email:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    try:
        # Send verification email via Supabase
        auth_service.resend_verification_email(email)
        logger.info(f"Verification email resent to: {email}")

        # Redirect back to verification page
        return RedirectResponse(
            url="/verify-email",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        return templates.TemplateResponse(
            "auth/verify_email.html",
            {
                "request": request,
                "email": email,
                "error": "Error resending verification email. Please try again."
            }
        )

@app.get("/auth/oauth/google")
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

    logger.info(f"Initiating Google OAuth login flow with URL: {oauth_url}")
    return RedirectResponse(url=oauth_url, status_code=303)

@app.get("/auth/v1/callback")
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

@app.get("/auth/callback")
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
            url=f"/login?error=Authentication+failed:+{error}",
            status_code=303
        )

    if not code:
        logger.error("OAuth callback missing code parameter")
        return RedirectResponse(
            url="/login?error=Authentication+failed",
            status_code=303
        )

    try:
        logger.info(f"Exchanging OAuth code for session")
        # Exchange code for session using our service method
        user = auth_service.exchange_code_for_session(code)

        if not user:
            logger.error("Failed to exchange OAuth code for session")
            return RedirectResponse(
                url="/login?error=Authentication+failed",
                status_code=303
            )

        # Set session data
        session_manager.set_session_user(request, user)

        # Redirect to next URL or dashboard
        next_url = request.query_params.get("next", "/dashboard")
        logger.info(f"User logged in via OAuth: {user.email} with subscription tier: {user.subscription_tier}")
        return RedirectResponse(url=next_url, status_code=303)

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Exception args: {e.args}")

        return RedirectResponse(
            url="/login?error=Authentication+failed",
            status_code=303
        )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Dashboard page.

    Args:
        request: The incoming request

    Returns:
        The dashboard page HTML
    """
    # Check if user is logged in
    if not session_manager.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    # Get user data
    user_id = request.session.get("user_id")

    # Try to get the current user from the auth service
    current_user = auth_service.get_current_user()

    # If we can't get the current user, try to create a user object from session data
    if not current_user:
        try:
            # Create a minimal user object from session data
            from app.auth.models import User
            from datetime import datetime

            current_user = User(
                id=user_id,
                email=request.session.get("email", ""),
                username=request.session.get("username", ""),
                subscription_tier=request.session.get("subscription_tier", "free"),
                created_at=datetime.now(),
                email_verified=True
            )

            logger.info(f"Created user object from session data: {current_user.email}")
        except Exception as e:
            logger.error(f"Error creating user from session: {str(e)}")
            # Clear session and redirect to login
            session_manager.clear_session(request)
            return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user
        }
    )

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """
    Profile page.

    Args:
        request: The incoming request

    Returns:
        The profile page HTML
    """
    # Check if user is logged in
    if not session_manager.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    # Get user data
    user_id = request.session.get("user_id")

    # Try to get the current user from the auth service
    current_user = auth_service.get_current_user()

    # If we can't get the current user, try to create a user object from session data
    if not current_user:
        try:
            # Create a minimal user object from session data
            from app.auth.models import User
            from datetime import datetime

            current_user = User(
                id=user_id,
                email=request.session.get("email", ""),
                username=request.session.get("username", ""),
                subscription_tier=request.session.get("subscription_tier", "free"),
                created_at=datetime.now(),
                email_verified=True
            )

            logger.info(f"Created user object from session data for profile: {current_user.email}")
        except Exception as e:
            logger.error(f"Error creating user from session for profile: {str(e)}")
            # Clear session and redirect to login
            session_manager.clear_session(request)
            return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user
        }
    )

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
