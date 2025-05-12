"""
Authentication routes for handling user signup, login, and verification.
"""
from datetime import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from app.config import config
from app.logging import get_logger
from app.exceptions import AuthenticationError, ValidationError
from auth.service_simple import AuthService
from app.services.session_service import get_session_service

# Get logger
logger = get_logger(__name__)

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Create router
router = APIRouter(tags=["auth"])

# Initialize services
auth_service = AuthService()
session_service = get_session_service()

# Helper function to get the base URL
def get_base_url(request):
    """Get the base URL for the application."""
    # Use the configured base URL
    if config.BASE_URL:
        return config.BASE_URL

    # Fall back to request headers if base URL is not configured
    host = request.headers.get("host", "localhost:8004")
    scheme = request.headers.get("x-forwarded-proto", "http")
    return f"{scheme}://{host}"

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render the register page."""
    # Check if user is already logged in
    if session_service.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...)
):
    """Handle user signup."""
    try:
        # Validate input
        if not email or not password or not username:
            raise ValidationError(
                message="All fields are required",
                field_errors={
                    "email": ["Email is required"] if not email else [],
                    "password": ["Password is required"] if not password else [],
                    "username": ["Username is required"] if not username else []
                }
            )

        # Register the user
        _, error = auth_service.sign_up(email, password, username)

        if error:
            logger.warning(f"Signup error for {email}: {error}")
            return templates.TemplateResponse(
                "auth/register.html",
                {"request": request, "error": error, "email": email, "username": username}
            )

        # Log successful registration
        logger.info(f"User registered successfully: {email}")

        # Registration successful - redirect to verification page with clear message
        return templates.TemplateResponse(
            "auth/verify_email.html",
            {
                "request": request,
                "email": email,
                "registration_success": True,
                "message": "Registration successful! Please check your email to verify your account."
            }
        )

    except ValidationError as e:
        logger.warning(f"Validation error during signup: {e.message}")
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": e.message, "email": email, "username": username}
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication error during signup: {e.message}")
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": e.message, "email": email, "username": username}
        )
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "An error occurred during signup", "email": email, "username": username}
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    # Check if user is already logged in
    if session_service.is_authenticated(request):
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    # Check for query parameters
    verified = request.query_params.get("verified") == "true"
    error = request.query_params.get("error")
    registered = request.query_params.get("registered") == "true"
    next_url = request.query_params.get("next", "/dashboard")

    # Check for unverified email error
    unverified_email = None
    message = None

    if error == "unverified_email":
        unverified_email = request.query_params.get("email")
        message = "Your email address has not been verified. Please check your inbox for the verification link."
        # Clear the error to avoid showing both error and message
        error = None

    # Log the parameters for debugging
    logger.info(f"Login page accessed with params: verified={verified}, error={error}, registered={registered}, unverified_email={unverified_email}")

    # Render the login page with appropriate context
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "verified": verified,
            "error": error,
            "message": message,
            "unverified_email": unverified_email,
            "registered": registered,
            "next": next_url
        }
    )

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle user login."""
    try:
        # Validate input
        if not email or not password:
            raise ValidationError(
                message="Email and password are required",
                field_errors={
                    "email": ["Email is required"] if not email else [],
                    "password": ["Password is required"] if not password else []
                }
            )

        # Authenticate the user
        user = auth_service.sign_in(email, password)

        if not user:
            raise AuthenticationError(
                message="Invalid email or password",
                detail={"email": email}
            )

        # Check if email is verified
        if not user.email_confirmed_at:
            # Log the unverified login attempt
            logger.info(f"Login attempt with unverified email: {email}")

            # Get the time since registration
            created_at = user.created_at
            now = datetime.now(created_at.tzinfo)
            hours_since_registration = (now - created_at).total_seconds() / 3600

            # Log the time since registration
            logger.info(f"Hours since registration: {hours_since_registration:.2f}")

            # If it's been more than 24 hours, suggest resending the verification email
            suggest_resend = hours_since_registration > 24

            # Redirect to login page with unverified_email parameter
            if suggest_resend:
                # If it's been more than 24 hours, redirect to verification page with suggest_resend
                return RedirectResponse(
                    url=f"/auth/verify-email?email={email}&from=login&suggest_resend={suggest_resend}",
                    status_code=HTTP_303_SEE_OTHER
                )
            else:
                # Otherwise, redirect to login page with unverified_email error
                return RedirectResponse(
                    url=f"/auth/login?error=unverified_email&email={email}",
                    status_code=HTTP_303_SEE_OTHER
                )

        # Set session data using session service
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.user_metadata.get("username", email.split("@")[0]),
            "subscription_tier": user.user_metadata.get("subscription_tier", "free")
        }
        session_service.set_user(request, user_data)

        # Log successful login
        logger.info(f"User logged in successfully: {email}")

        # Redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)

    except ValidationError as e:
        logger.warning(f"Validation error during login: {e.message}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": e.message, "email": email}
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication error during login: {e.message}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": e.message, "email": email}
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "An error occurred during login", "email": email}
        )

@router.get("/oauth/google")
async def google_login():
    """Initiate Google OAuth login."""
    try:
        # Generate OAuth URL
        oauth_url = auth_service.get_oauth_url("google")

        # Log the OAuth URL for debugging
        logger.info(f"Generated Google OAuth URL: {oauth_url}")

        # Redirect to Google OAuth
        return RedirectResponse(url=oauth_url)

    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        return RedirectResponse(url="/auth/login?error=google_oauth_error")

@router.get("/callback")
async def auth_callback(request: Request, code: str = None):
    """Handle OAuth callback."""
    if not code:
        return RedirectResponse(url="/auth/login?error=missing_code")

    try:
        # Log the code for debugging
        logger.info(f"Received OAuth callback with code: {code}")

        # Exchange code for session
        user = auth_service.exchange_code_for_session(code)

        # Log the user data for debugging
        logger.info(f"Authenticated user: {user.email if user else 'None'}")

        if not user:
            return RedirectResponse(url="/auth/login?error=authentication_failed")

        # Get username from metadata or use email prefix as fallback
        username = user.user_metadata.get("username")
        oauth_provider = None

        # Log the user object for debugging
        logger.info(f"User object: {user}")

        # Try to extract identity information
        try:
            if hasattr(user, "identities") and user.identities:
                logger.info(f"User has identities: {user.identities}")

                # Try to get name and provider from identity provider (Google)
                for identity in user.identities:
                    # Log the identity object for debugging
                    logger.info(f"Processing identity: {identity}")

                    # Check if identity is a dictionary or an object
                    if isinstance(identity, dict):
                        provider = identity.get("provider")
                        if provider == "google":
                            oauth_provider = "google"
                            identity_data = identity.get("identity_data", {})
                            if identity_data:
                                username = identity_data.get("name") or identity_data.get("full_name") or username
                                # Log the identity data for debugging
                                logger.info(f"Google identity data (dict): {identity_data}")
                            break
                    else:
                        # Handle the case where identity is an object
                        try:
                            # Try different ways to access the provider
                            provider = None
                            if hasattr(identity, "provider"):
                                provider = identity.provider
                            elif hasattr(identity, "get") and callable(identity.get):
                                provider = identity.get("provider")

                            if provider == "google":
                                oauth_provider = "google"

                                # Try different ways to access identity data
                                identity_data = None
                                if hasattr(identity, "identity_data"):
                                    identity_data = identity.identity_data
                                elif hasattr(identity, "get") and callable(identity.get):
                                    identity_data = identity.get("identity_data", {})

                                if identity_data:
                                    # Try different ways to access name
                                    if isinstance(identity_data, dict):
                                        name = identity_data.get("name") or identity_data.get("full_name")
                                        if name:
                                            username = name
                                    elif hasattr(identity_data, "name"):
                                        username = identity_data.name
                                    elif hasattr(identity_data, "full_name"):
                                        username = identity_data.full_name

                                    # Log the identity data for debugging
                                    logger.info(f"Google identity data (object): {identity_data}")
                                break
                        except Exception as e:
                            logger.error(f"Error processing identity object: {str(e)}")
                            # Continue to next identity
        except Exception as e:
            logger.error(f"Error processing user identities: {str(e)}")

        # If we still don't have a username, use email prefix
        if not username:
            username = user.email.split("@")[0]

        # Log the final username
        logger.info(f"Final username: {username}")

        # Store user data in session using session service
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": username,
            "subscription_tier": user.user_metadata.get("subscription_tier", "free"),
            "oauth_provider": oauth_provider
        }
        session_service.set_user(request, user_data)

        # Log session data for debugging
        logger.info(f"Session data: username={username}, oauth_provider={oauth_provider}, subscription_tier={user.user_metadata.get('subscription_tier', 'free')}")

        # Log OAuth provider for debugging
        logger.info(f"OAuth provider: {oauth_provider}")

        # Log session data for debugging
        logger.info(f"Set session data: user_id={user.id}, email={user.email}, username={username}")

        # Send welcome email for Google sign-ups
        try:
            from app.services.email.email_service_simple import EmailService
            email_service = EmailService()

            # Log email configuration
            logger.info(f"Email configuration: SMTP_SERVER={email_service.smtp_server}, SMTP_PORT={email_service.smtp_port}, SMTP_USER={email_service.smtp_username}, FROM_EMAIL={email_service.from_email}, FROM_NAME={email_service.from_name}")
            logger.info(f"Is email configured: {email_service.is_configured}")

            # Send welcome email
            result = email_service.send_welcome_email(user.email, is_oauth=True)

            if result:
                logger.info(f"Welcome email sent to Google user: {user.email}")
            else:
                logger.error(f"Failed to send welcome email to Google user: {user.email}")
        except Exception as e:
            logger.error(f"Error sending welcome email to Google user: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        # Redirect to dashboard
        return RedirectResponse(url="/dashboard")

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(url=f"/auth/login?error=oauth_callback_error")

@router.get("/logout")
async def logout(request: Request):
    """Handle user logout."""
    # Get user email for logging
    user_email = request.session.get("email", "unknown")

    # Clear session using session service
    session_service.clear_session(request)

    # Sign out from Supabase
    auth_service.sign_out()

    # Log the logout
    logger.info(f"User logged out: {user_email}")

    # Redirect to home page
    return RedirectResponse(url="/")

@router.get("/verify")
async def verify_email(request: Request, token: str = None):
    """Handle email verification."""
    if not token:
        return RedirectResponse(url="/auth/login?error=missing_token")

    try:
        # This is handled by Supabase automatically
        # Log the verification attempt
        logger.info(f"Email verification with token: {token[:10]}...")

        # Redirect to login with a clear success message
        return templates.TemplateResponse(
            "auth/verification_success.html",
            {"request": request}
        )

    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return RedirectResponse(url="/auth/login?error=verification_failed")

@router.get("/verify-email")
async def verify_email_page(request: Request, email: str = None):
    """Render the email verification page."""
    # Check if this is a redirect from login with unverified email
    from_login = request.query_params.get("from") == "login"

    # Check if this is a resend success
    resend_success = request.query_params.get("resend") == "success"

    # Check if we should suggest resending the verification email
    suggest_resend = request.query_params.get("suggest_resend") == "True"

    # Log the request
    logger.info(f"Verify email page accessed for email: {email}, from_login: {from_login}, resend_success: {resend_success}, suggest_resend: {suggest_resend}")

    # Determine the appropriate message
    message = None
    if from_login:
        message = "You need to verify your email before you can log in."
        if suggest_resend:
            message += " It looks like your verification link may have expired. You can request a new one below."

    return templates.TemplateResponse(
        "auth/verify_email.html",
        {
            "request": request,
            "email": email,
            "from_login": from_login,
            "resend_success": resend_success,
            "suggest_resend": suggest_resend,
            "message": message
        }
    )

@router.get("/resend-verification")
async def resend_verification_page(request: Request, email: str = None):
    """Render the resend verification page."""
    # Log the request
    logger.info(f"Resend verification page accessed for email: {email}")

    return templates.TemplateResponse(
        "auth/resend_verification.html",
        {"request": request, "email": email}
    )

@router.get("/rate-limited")
async def rate_limited(request: Request):
    """Handle rate limiting."""
    # Get retry_after from query parameters
    retry_after = request.query_params.get("retry_after", "60")

    # Log the rate limit
    logger.warning(f"Rate limited page accessed, retry after: {retry_after} seconds")

    # Render the rate limited page
    return templates.TemplateResponse(
        "auth/rate_limited.html",
        {"request": request, "retry_after": retry_after}
    )

@router.post("/resend-verification")
async def resend_verification(request: Request, email: str = Form(...)):
    """Resend verification email."""
    try:
        # Validate email
        if not email:
            raise ValidationError(
                message="Email is required",
                field_errors={"email": ["Email is required"]}
            )

        # Check if user exists
        user = auth_service.get_user_by_email(email)

        if not user:
            logger.warning(f"Resend verification attempted for non-existent email: {email}")
            return templates.TemplateResponse(
                "auth/resend_verification.html",
                {
                    "request": request,
                    "email": email,
                    "success": True,  # Don't reveal that the email doesn't exist
                    "message": "If your email exists in our system, a verification link has been sent."
                }
            )

        # Check if email is already verified
        if user.email_confirmed_at:
            logger.info(f"Resend verification attempted for already verified email: {email}")
            return templates.TemplateResponse(
                "auth/resend_verification.html",
                {
                    "request": request,
                    "email": email,
                    "success": True,
                    "message": "Your email is already verified. You can now log in."
                }
            )

        # Resend verification email
        result = auth_service.resend_verification_email(email)

        if not result:
            logger.error(f"Failed to resend verification email to: {email}")
            return templates.TemplateResponse(
                "auth/resend_verification.html",
                {
                    "request": request,
                    "email": email,
                    "error": "Failed to resend verification email. Please try again later."
                }
            )

        # Log success
        logger.info(f"Verification email resent to: {email}")

        # Redirect to verification page
        return RedirectResponse(
            url=f"/auth/verify-email?email={email}&resend=success",
            status_code=HTTP_303_SEE_OTHER
        )

    except ValidationError as e:
        logger.warning(f"Validation error during resend verification: {e.message}")
        return templates.TemplateResponse(
            "auth/resend_verification.html",
            {"request": request, "error": e.message, "email": email}
        )
    except Exception as e:
        logger.error(f"Unexpected error during resend verification: {str(e)}")
        return templates.TemplateResponse(
            "auth/resend_verification.html",
            {"request": request, "error": "An error occurred. Please try again later.", "email": email}
        )
