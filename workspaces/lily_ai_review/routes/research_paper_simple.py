"""
Research paper routes for Lily AI.
"""
import logging
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from app.utils.session_helpers_simple import get_session_manager
from app.services.billing.subscription_service_simple import SubscriptionService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="/home/admin/projects/lily_ai/templates")

# Create router
router = APIRouter(tags=["research_paper"])

# Initialize services
session_manager = get_session_manager()
subscription_service = SubscriptionService()

@router.get("/research-paper", response_class=HTMLResponse)
async def research_paper_page(request: Request):
    """Render the research paper creation page."""
    # Check if user is logged in
    if not session_manager.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")

    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user_id)

    # Check if user has papers remaining
    total_papers_remaining = subscription.get("total_papers_remaining", 0)

    if total_papers_remaining <= 0:
        # If user is premium, redirect to buy credits page
        if subscription.get("subscription_tier") == "premium":
            return RedirectResponse(url="/billing/buy-credits", status_code=HTTP_303_SEE_OTHER)
        else:
            # If user is free, redirect to subscription page
            return RedirectResponse(url="/subscription", status_code=HTTP_303_SEE_OTHER)

    # User has papers remaining, show the research paper form
    return templates.TemplateResponse(
        "research_paper.html",
        {
            "request": request,
            "user": session_manager.get_user(request),
            "subscription": subscription,
            "papers_remaining": subscription.get("papers_remaining", 0),
            "additional_papers_remaining": subscription.get("additional_credits_remaining", 0),
            "total_papers_remaining": total_papers_remaining
        }
    )

@router.post("/research-paper", response_class=RedirectResponse)
async def create_research_paper(
    request: Request,
    topic: str = Form(...),
    description: str = Form(None)
):
    """Create a new research paper."""
    # Check if user is logged in
    if not session_manager.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")

    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user_id)

    # Check if user has papers remaining
    total_papers_remaining = subscription.get("total_papers_remaining", 0)

    if total_papers_remaining <= 0:
        # If user is premium, redirect to buy credits page
        if subscription.get("subscription_tier") == "premium":
            return RedirectResponse(url="/billing/buy-credits", status_code=HTTP_303_SEE_OTHER)
        else:
            # If user is free, redirect to subscription page
            return RedirectResponse(url="/subscription", status_code=HTTP_303_SEE_OTHER)

    try:
        # Increment papers used count
        success = subscription_service.increment_papers_used(user_id)

        if not success:
            logger.error(f"Failed to increment papers used for user {user_id}")
            # Redirect to error page
            return RedirectResponse(url="/dashboard?error=paper_creation_failed", status_code=HTTP_303_SEE_OTHER)

        # For now, just redirect to dashboard with success message
        # In a real implementation, you would create a job and redirect to the paper status page
        return RedirectResponse(url="/dashboard?paper_created=true", status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error creating research paper: {str(e)}")
        return RedirectResponse(url="/dashboard?error=paper_creation_failed", status_code=HTTP_303_SEE_OTHER)
