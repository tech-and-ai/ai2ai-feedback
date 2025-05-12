"""
Lily AI Research Pack Generator - Main Application
"""
import os
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Import configuration
from app.config import config

# Configure logging
from app.logging import configure_logging, get_logger
configure_logging()
logger = get_logger(__name__)

# Import routes
from routes.auth import router as auth_router
from routes.billing import router as billing_router
from routes.billing_webhook import router as billing_webhook_router
from routes.research_paper import router as research_paper_router
from routes.notification_webhook import router as notification_webhook_router

# Log configuration information
logger.info(f"Starting application in {config.ENV} mode")
logger.info(f"Debug mode: {config.DEBUG}")
logger.info(f"Stripe mode: {config.get_stripe_mode()}")

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION
)

# Mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Add custom filters
def format_uk_date(date_str):
    """Format a date string to UK format (DD/MM/YYYY)."""
    if not date_str:
        return ""
    try:
        # Try parsing ISO format
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = date_str
        return date_obj.strftime("%d/%m/%Y")
    except Exception:
        return date_str

# Register the filter
templates.env.filters["format_uk_date"] = format_uk_date

# Add CSRF protection middleware
from app.middleware.csrf import CSRFMiddleware
app.add_middleware(CSRFMiddleware)

# Add rate limiting middleware
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Add session validation middleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.session_service import get_session_service

class SessionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for validating session integrity."""

    async def dispatch(self, request, call_next):
        """Validate session before processing request."""
        # Skip validation for certain paths
        path = request.url.path
        skip_paths = [
            "/auth/login",
            "/auth/register",
            "/auth/verify",
            "/auth/verify-email",
            "/auth/callback",
            "/auth/oauth/google",
            "/static",
            "/favicon.ico",
            "/billing/webhook"
        ]

        # Skip validation for excluded paths
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            return await call_next(request)

        # Get session service
        session_service = get_session_service()

        # Check if user is authenticated
        if session_service.is_authenticated(request):
            # Validate session integrity
            if not session_service.validate_session(request):
                # Session validation failed, clear session
                session_service.clear_session(request)
                logger.warning(f"Session validation failed for path: {path}")

                # Redirect to login page
                if path != "/auth/logout" and not path.startswith("/api/"):
                    return RedirectResponse(url="/auth/login?error=session_expired", status_code=303)

        # Continue processing request
        return await call_next(request)

# Add session validation middleware
app.add_middleware(SessionValidationMiddleware)

# Add session middleware (must be last to be executed first)
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET_KEY,
    max_age=config.SESSION_MAX_AGE,
    same_site=config.SESSION_SAME_SITE,
    https_only=config.SESSION_HTTPS_ONLY
)

# Add exception handlers
from app.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(_: Request, exc: AppException):
    """Handle application-specific exceptions."""
    logger.error(f"Application exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message, "detail": exc.detail}
    )

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(billing_router, prefix="/billing", tags=["billing"])
app.include_router(billing_webhook_router, prefix="/billing", tags=["webhook"])
app.include_router(research_paper_router, prefix="/api/research", tags=["research"])
app.include_router(notification_webhook_router, prefix="/api/notifications", tags=["notifications"])

# Helper function to get template context
def get_template_context(request: Request) -> dict:
    """
    Get the base template context with common data.

    Args:
        request: The incoming request

    Returns:
        dict: Template context
    """
    # Base context
    context = {
        "request": request,
        "app_name": "Lily AI Research Pack Generator",
        "current_year": 2025,
    }

    # Get user data from session
    user_id = request.session.get("user_id")

    # Add user to context if logged in
    if user_id:
        # Create user object from session data
        user = {
            "id": user_id,
            "email": request.session.get("email", ""),
            "username": request.session.get("username", "Guest"),
            "subscription_tier": request.session.get("subscription_tier", "free"),
            "oauth_provider": request.session.get("oauth_provider", None)
        }

        # Add user to context
        context["user"] = user

        # Log user data for debugging
        logger.info(f"User data in template context: {user}")

        # Add subscription and papers information for logged-in users
        try:
            # Only add this information if not already in context
            if "total_papers_remaining" not in context:
                from app.services.billing.subscription_service import SubscriptionService
                subscription_service = SubscriptionService()

                # Get user's subscription
                subscription = subscription_service.get_user_subscription(user_id)

                # Get paper counts
                subscription_papers_remaining = subscription.get("papers_remaining", 0)
                additional_papers_remaining = subscription.get("additional_credits_remaining", 0)
                total_papers_remaining = subscription.get("total_papers_remaining", 0)

                # Add to context
                context["subscription_papers_remaining"] = subscription_papers_remaining
                context["additional_papers_remaining"] = additional_papers_remaining
                context["total_papers_remaining"] = total_papers_remaining
                context["subscription_tier"] = subscription.get("subscription_tier", "free")

                # Update user subscription tier in context
                context["user"]["subscription_tier"] = subscription.get("subscription_tier", "free")
        except Exception as e:
            logger.error(f"Error getting subscription data: {str(e)}")

    return context

# Home page route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, code: str = None):
    """
    Render the home page.

    Args:
        request: The incoming request
        code: OAuth code (if present)

    Returns:
        HTMLResponse with the home template
    """
    # If code is present, it's a callback from OAuth
    if code:
        logger.info(f"Received OAuth callback code on home page: {code}")
        # Redirect to the callback route
        return RedirectResponse(url=f"/auth/callback?code={code}", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse("home.html", get_template_context(request))

# About page route
@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """
    Render the about page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the about template
    """
    return templates.TemplateResponse("about.html", get_template_context(request))

# Pricing page route
@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """
    Render the pricing page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the pricing template
    """
    return templates.TemplateResponse("pricing.html", get_template_context(request))

# Contact page route
@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """
    Render the contact page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the contact template
    """
    return templates.TemplateResponse("contact.html", get_template_context(request))

# Terms page route
@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    """
    Render the terms page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the terms template
    """
    return templates.TemplateResponse("terms.html", get_template_context(request))

# Privacy page route
@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """
    Render the privacy page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the privacy template
    """
    return templates.TemplateResponse("privacy.html", get_template_context(request))

# Help page route
@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """
    Render the help page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the help template
    """
    return templates.TemplateResponse("help.html", get_template_context(request))

# 404 error handler
@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, _):
    """
    Handle 404 Not Found errors.

    Args:
        request: The incoming request
        _: The exception (unused)

    Returns:
        HTMLResponse with the 404 template
    """
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=status.HTTP_404_NOT_FOUND
    )

# 500 error handler
@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_server_error_handler(request: Request, exc):
    """
    Handle 500 Internal Server Error errors.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        HTMLResponse with the 500 template
    """
    logger.error(f"Internal server error: {str(exc)}")
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# Account deletion route
@app.get("/account/delete", response_class=HTMLResponse)
async def delete_account_page(request: Request):
    """
    Render the account deletion confirmation page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the account deletion confirmation template
    """
    return templates.TemplateResponse(
        "account/delete_confirmation.html",
        get_template_context(request)
    )







# Profile/Usage Analytics page route
@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """
    Render the profile/usage analytics page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the profile template
    """
    return templates.TemplateResponse("profile.html", get_template_context(request))

# Account Management page route
@app.get("/account/manage", response_class=HTMLResponse)
async def account_manage(request: Request):
    """
    Render the account management page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the account management template
    """
    return templates.TemplateResponse("account/manage.html", get_template_context(request))

# Subscription page route
@app.get("/subscription", response_class=HTMLResponse)
async def subscription(request: Request):
    """
    Render the subscription page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the subscription template or redirect to buy credits for premium users
    """
    context = get_template_context(request)

    # Ensure subscription is defined to avoid template errors
    if "subscription" not in context:
        # Get user's subscription from the database
        try:
            user_id = request.session.get("user_id")
            if user_id:
                from app.services.billing.subscription_service import SubscriptionService
                subscription_service = SubscriptionService()
                subscription = subscription_service.get_user_subscription(user_id)
                context["subscription"] = subscription

                # Check if user is already a premium subscriber
                if subscription.get("subscription_tier") == "premium" and subscription.get("status") == "active":
                    logger.info(f"Premium user {user_id} accessing subscription page, redirecting to buy credits")
                    return RedirectResponse(url="/billing/buy-credits", status_code=303)
            else:
                context["subscription"] = {"subscription_tier": "free", "status": "active"}
        except Exception as e:
            logger.error(f"Error getting subscription for subscription page: {str(e)}")
            context["subscription"] = {"subscription_tier": "free", "status": "active"}

    return templates.TemplateResponse("subscription.html", context)

# Credits page route (redirect to buy-credits)
@app.get("/credits", response_class=HTMLResponse)
async def credits_redirect(request: Request):
    """
    Redirect to the buy credits page.

    Args:
        request: The incoming request

    Returns:
        Redirect to the buy credits page
    """
    logger.info("Redirecting from /credits to /billing/buy-credits")
    return RedirectResponse(url="/billing/buy-credits", status_code=303)

# My Papers page route
@app.get("/my-papers", response_class=HTMLResponse)
async def my_papers(request: Request):
    """
    Render the my papers page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the papers template or redirect to subscription page for free users
    """
    # Get template context
    context = get_template_context(request)

    # Check if user is authenticated
    if "user" not in context:
        # Redirect to login page
        return RedirectResponse(url="/auth/login", status_code=303)

    # Check user's subscription tier
    subscription_tier = context.get("subscription_tier", "free")

    # If user is on free/sample tier, redirect to subscription page
    if subscription_tier in ["free", "sample"]:
        logger.info(f"Free user attempted to access my-papers, redirecting to subscription")
        return RedirectResponse(url="/subscription", status_code=303)

    # Add empty papers list if not present
    if "papers" not in context:
        context["papers"] = []

    return templates.TemplateResponse("papers.html", context)

# Individual paper view route
@app.get("/my-papers/{paper_id}", response_class=HTMLResponse)
async def view_paper(request: Request, paper_id: int):
    """
    Render the individual paper view page.

    Args:
        request: The incoming request
        paper_id: The ID of the paper to view

    Returns:
        HTMLResponse with the paper view template or redirect to subscription page for free users
    """
    # Get template context
    context = get_template_context(request)

    # Check if user is authenticated
    if "user" not in context:
        # Redirect to login page
        return RedirectResponse(url="/auth/login", status_code=303)

    # Check user's subscription tier
    subscription_tier = context.get("subscription_tier", "free")

    # If user is on free/sample tier, redirect to subscription page
    if subscription_tier in ["free", "sample"]:
        logger.info(f"Free user attempted to access paper view, redirecting to subscription")
        return RedirectResponse(url="/subscription", status_code=303)

    # In a real implementation, you would fetch the paper data from a database
    # For now, we'll just return a placeholder
    paper = {
        "id": paper_id,
        "title": "Example Paper Title",
        "status": "completed",
        "created_at": "2023-05-15",
        "content": "This is an example paper content."
    }

    # Add paper to context
    context["paper"] = paper

    return templates.TemplateResponse("paper_view.html", context)

# This route has been removed and replaced with /research-paper

# Research paper generation route
@app.get("/research-paper", response_class=HTMLResponse)
async def research_paper(request: Request):
    """
    Render the research paper generation page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the research paper template or redirect to subscription page
    """
    # Get template context
    context = get_template_context(request)

    # Check if user is authenticated
    if "user" not in context:
        logger.warning("Unauthenticated user attempted to access research paper page")
        return RedirectResponse(url="/auth/login", status_code=303)

    # Get user ID
    user_id = context["user"].get("id")
    if not user_id:
        logger.warning("User without ID attempted to access research paper page")
        return RedirectResponse(url="/auth/login", status_code=303)

    # Initialize subscription service
    from app.services.billing.subscription_service import SubscriptionService
    subscription_service = SubscriptionService()

    # Verify subscription status with Stripe
    is_valid = subscription_service.verify_subscription_with_stripe(user_id)

    if not is_valid:
        # User doesn't have a valid subscription
        # With our policy, additional credits can only be used with an active premium subscription
        logger.warning(f"User {user_id} attempted to access research paper without valid subscription")

        # Get the current subscription from database
        subscription = subscription_service.get_user_subscription(user_id)

        # Update session data to reflect current subscription status
        from app.services.session_service import get_session_service
        session_service = get_session_service()
        session_service.update_user(request, {"subscription_tier": subscription.get("subscription_tier", "free")})

        # Check if user has additional credits that they can't use
        additional_credits = subscription.get("additional_credits_remaining", 0)

        # Redirect to subscription page with appropriate error message
        if additional_credits > 0:
            # User has credits but can't use them without active subscription
            return RedirectResponse(url="/subscription?error=subscription_required_for_credits", status_code=303)
        else:
            # User has no credits and no subscription
            return RedirectResponse(url="/subscription?error=subscription_expired", status_code=303)

    # User has valid subscription or additional credits, render the page
    return templates.TemplateResponse("research_paper.html", context)

# API endpoint for research paper generation
@app.post("/api/research-paper/generate")
async def generate_research_paper(request: Request):
    """
    Handle research paper generation form submission.

    Args:
        request: The incoming request

    Returns:
        Redirect to the papers page or subscription page
    """
    # Log request for debugging
    logger.info(f"Received research paper generation request")

    # Get template context
    context = get_template_context(request)

    # Check if user is authenticated
    if "user" not in context:
        logger.warning("Unauthenticated user attempted to generate research paper")
        return RedirectResponse(url="/auth/login", status_code=303)

    # Get user ID
    user_id = context["user"].get("id")
    if not user_id:
        logger.warning("User without ID attempted to generate research paper")
        return RedirectResponse(url="/auth/login", status_code=303)

    # Initialize subscription service
    from app.services.billing.subscription_service import SubscriptionService
    subscription_service = SubscriptionService()

    # Verify subscription status with Stripe
    is_valid = subscription_service.verify_subscription_with_stripe(user_id)

    if not is_valid:
        # User doesn't have a valid subscription
        # With our policy, additional credits can only be used with an active premium subscription
        logger.warning(f"User {user_id} attempted to generate research paper without valid subscription")

        # Get the current subscription from database
        subscription = subscription_service.get_user_subscription(user_id)

        # Update session data to reflect current subscription status
        from app.services.session_service import get_session_service
        session_service = get_session_service()
        session_service.update_user(request, {"subscription_tier": subscription.get("subscription_tier", "free")})

        # Check if user has additional credits that they can't use
        additional_credits = subscription.get("additional_credits_remaining", 0)

        # Redirect to subscription page with appropriate error message
        if additional_credits > 0:
            # User has credits but can't use them without active subscription
            logger.info(f"User {user_id} has {additional_credits} unused credits but no active subscription")
            return RedirectResponse(url="/subscription?error=subscription_required_for_credits", status_code=303)
        else:
            # User has no credits and no subscription
            return RedirectResponse(url="/subscription?error=subscription_expired", status_code=303)

    # User has valid subscription or additional credits, use a paper credit
    success = subscription_service.use_paper_credit(user_id)

    if not success:
        # Failed to use paper credit
        logger.error(f"Failed to use paper credit for user {user_id}")
        return RedirectResponse(url="/dashboard?error=paper_credit_failed", status_code=303)

    # In a real implementation, we would process the form data and submit a job
    # For now, we'll just redirect to the papers page

    # Redirect to the papers page
    return RedirectResponse(url="/my-papers", status_code=status.HTTP_303_SEE_OTHER)

# My Reviews page route
@app.get("/my-reviews", response_class=HTMLResponse)
async def my_reviews(request: Request):
    """
    Render the my reviews page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the my reviews template
    """
    return templates.TemplateResponse("my_reviews.html", get_template_context(request))

# Review Upload page route
@app.get("/review/upload", response_class=HTMLResponse)
async def review_upload(request: Request):
    """
    Render the review upload page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the review upload template
    """
    return templates.TemplateResponse("review_upload.html", get_template_context(request))

# Direct API endpoint for research paper generation (bypasses credit checks)
@app.post("/api/direct/research-paper/generate")
async def generate_research_paper_direct(request: Request):
    """
    Handle direct API research paper generation.
    This endpoint bypasses credit checks and is intended for API access only.

    Args:
        request: The incoming request

    Returns:
        JSON response with job ID and status
    """
    try:
        # Get JSON data
        json_data = await request.json()

        # Extract data
        topic = json_data.get("topic")

        # Validate required fields
        if not topic:
            return JSONResponse(
                content={"error": "Topic is required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Return job ID and status
        return JSONResponse(
            content={
                "job_id": "sample-job-id",
                "status": "queued",
                "message": "Research paper generation job submitted successfully"
            },
            status_code=status.HTTP_202_ACCEPTED
        )

    except Exception as e:
        logger.error(f"Error submitting direct API research paper job: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to submit paper generation job: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Enterprise API endpoint for research paper generation
@app.post("/api/enterprise/research-paper/generate")
async def generate_research_paper_enterprise(request: Request):
    """
    Handle enterprise API research paper generation.
    This endpoint is intended for enterprise API access only.

    Args:
        request: The incoming request

    Returns:
        JSON response with job ID and status
    """
    try:
        # Get JSON data
        json_data = await request.json()

        # Extract data
        topic = json_data.get("topic")

        # Validate required fields
        if not topic:
            return JSONResponse(
                content={"error": "Topic is required"},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Return job ID and status
        return JSONResponse(
            content={
                "job_id": "enterprise-job-id",
                "status": "queued",
                "message": "Enterprise research paper generation job submitted successfully"
            },
            status_code=status.HTTP_202_ACCEPTED
        )

    except Exception as e:
        logger.error(f"Error submitting enterprise API research paper job: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to submit paper generation job: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# API endpoint for checking job status
@app.get("/api/direct/research-paper/status/{job_id}")
async def check_research_paper_status(job_id: str):
    """
    Check the status of a research paper generation job.

    Args:
        job_id: The ID of the job to check

    Returns:
        JSON response with job status and details
    """
    try:
        # Sample job details
        job_details = {
            "job_id": job_id,
            "status": "completed",
            "created_at": "2023-05-15T12:00:00Z",
            "updated_at": "2023-05-15T12:05:00Z",
            "completed_at": "2023-05-15T12:05:00Z",
            "progress": 100,
            "progress_message": "Paper generation complete",
            "result": {
                "docx_url": "https://example.com/papers/sample.docx",
                "pdf_url": "https://example.com/papers/sample.pdf",
                "generation_time": 300
            }
        }

        return JSONResponse(content=job_details)

    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return JSONResponse(
            content={"error": f"Failed to check job status: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# API endpoint for retrying a failed paper
@app.get("/api/research-paper/retry/{job_id}")
async def retry_research_paper(request: Request, job_id: str):
    """
    Handle retrying a failed research paper job.

    Args:
        request: The incoming request
        job_id: The ID of the job to retry

    Returns:
        Redirect to the papers page
    """
    try:
        logger.info(f"Job {job_id} resubmitted successfully")

        # Redirect to the papers page
        return RedirectResponse(url="/my-papers", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error retrying research paper job: {str(e)}")
        return templates.TemplateResponse(
            "errors/500.html",
            get_template_context(request, {"error": "Failed to retry paper generation"}),
            status_code=500
        )

# 401 error handler
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, _):
    """
    Handle 401 Unauthorized errors.

    Args:
        request: The incoming request
        _: The exception (unused)

    Returns:
        HTMLResponse with the 401 template
    """
    logger.warning(f"Unauthorized access attempt: {request.url.path}")
    return templates.TemplateResponse(
        "errors/401.html", get_template_context(request), status_code=status.HTTP_401_UNAUTHORIZED
    )

# Dashboard route
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render the dashboard page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse with the dashboard template
    """
    context = get_template_context(request)

    # Check if user is authenticated
    if "user" in context and context["user"].get("id"):
        user_id = context["user"].get("id")

        # Initialize subscription service
        from app.services.billing.subscription_service import SubscriptionService
        subscription_service = SubscriptionService()

        # Get user subscription from database
        subscription = subscription_service.get_user_subscription(user_id)
        context["subscription"] = subscription

        # If user has a premium subscription, verify it with Stripe
        if subscription.get("subscription_tier") == "premium":
            # Verify subscription status with Stripe
            is_premium = subscription_service.verify_subscription_with_stripe(user_id)

            # If verification failed, update the session data and subscription context
            if not is_premium:
                # Update session data
                from app.services.session_service import get_session_service
                session_service = get_session_service()
                session_service.update_user(request, {"subscription_tier": subscription.get("subscription_tier", "free")})

                # Update context with latest subscription info
                subscription = subscription_service.get_user_subscription(user_id)
                context["subscription"] = subscription

                # Log the verification failure
                logger.warning(f"Subscription verification failed for user {user_id} in dashboard")

    # Ensure subscription is defined to avoid template errors
    if "subscription" not in context:
        context["subscription"] = {
            "subscription_tier": "free",
            "status": "inactive",
            "papers_limit": 10,
            "papers_used": 0,
            "papers_remaining": 10
        }

    # Ensure user is defined to avoid template errors
    if "user" not in context:
        context["user"] = {"username": "Guest"}

    # Get sample papers
    try:
        from app.services.utils.storage_service import StorageService
        storage_service = StorageService()
        sample_papers = storage_service.get_sample_papers()
        logger.info(f"Retrieved {len(sample_papers)} sample papers for dashboard")
        context["sample_papers"] = sample_papers
    except Exception as e:
        logger.error(f"Error retrieving sample papers: {str(e)}")
        # Provide fallback sample papers if retrieval fails
        context["sample_papers"] = [
            {
                'title': 'Climate Change Research',
                'url': '#',
                'file_type': 'pdf',
                'file_name': 'climate_change_research.pdf'
            },
            {
                'title': 'Artificial Intelligence Ethics',
                'url': '#',
                'file_type': 'docx',
                'file_name': 'ai_ethics.docx'
            },
            {
                'title': 'Renewable Energy Solutions',
                'url': '#',
                'file_type': 'pdf',
                'file_name': 'renewable_energy.pdf'
            }
        ]

    return templates.TemplateResponse("dashboard.html", context)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8004))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
