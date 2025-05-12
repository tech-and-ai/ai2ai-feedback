"""
Research paper routes for Lily AI.

This module provides routes for creating and managing research papers.
"""
import logging
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from auth.dependencies import get_current_user
from app.services.billing.subscription_service_new import SubscriptionService
from app.services.queue_engine.queue_manager import QueueManager

# Set up logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["research_paper"])

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize services
subscription_service = SubscriptionService()
queue_manager = QueueManager()

@router.get("/research-paper", response_class=HTMLResponse)
async def research_paper_page(request: Request, user=Depends(get_current_user)):
    """
    Render the research paper creation page.
    
    Args:
        request: The incoming request
        user: The current authenticated user
        
    Returns:
        HTMLResponse with the research paper template
    """
    # Check if user can create a paper
    can_create = subscription_service.can_create_paper(user.get("id"))
    
    if not can_create:
        # Redirect to subscription page if user can't create a paper
        return RedirectResponse(url="/subscription?error=no_credits", status_code=303)
    
    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user.get("id"))
    
    # Add common template context
    context = {
        "request": request,
        "user": user,
        "subscription": subscription.to_dict(),
        "papers_remaining": subscription.papers_remaining,
        "additional_papers_remaining": subscription.additional_credits,
        "total_papers_remaining": subscription.papers_remaining + subscription.additional_credits
    }
    
    return templates.TemplateResponse("research_paper.html", context)

@router.post("/research-paper", response_class=RedirectResponse)
async def create_research_paper(
    request: Request,
    topic: str = Form(...),
    description: str = Form(None),
    user=Depends(get_current_user)
):
    """
    Create a new research paper.
    
    Args:
        request: The incoming request
        topic: The research paper topic
        description: Additional details about the research (optional)
        user: The current authenticated user
        
    Returns:
        Redirect to the paper status page
    """
    # Check if user can create a paper
    can_create = subscription_service.can_create_paper(user.get("id"))
    
    if not can_create:
        # Redirect to subscription page if user can't create a paper
        return RedirectResponse(url="/subscription?error=no_credits", status_code=303)
    
    try:
        # Create a new job for the research paper
        job_id = queue_manager.create_job(
            job_type="research_paper",
            user_id=user.get("id"),
            params={
                "topic": topic,
                "description": description
            },
            priority=1  # Normal priority
        )
        
        if not job_id:
            logger.error(f"Failed to create job for user {user.get('id')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create research paper job"
            )
        
        # Increment papers used count
        success = subscription_service.increment_papers_used(user.get("id"))
        
        if not success:
            logger.error(f"Failed to increment papers used for user {user.get('id')}")
            # Continue anyway, as the job has been created
        
        # Redirect to the paper status page
        return RedirectResponse(url=f"/my-papers/{job_id}", status_code=303)
    
    except Exception as e:
        logger.error(f"Error creating research paper: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the research paper"
        )
