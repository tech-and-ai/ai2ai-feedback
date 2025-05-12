"""
Notification webhook handler for processing database events.
"""
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any

from app.logging import get_logger
from app.services.email.email_service import EmailService
from app.services.auth.auth_service import AuthService

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["notifications"])

# Initialize services
email_service = EmailService()
auth_service = AuthService()

@router.post("/webhook", include_in_schema=True)
async def notification_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle notification webhook events from database triggers.

    This endpoint receives webhook events from database triggers and
    processes them accordingly.

    Args:
        request: The incoming request
        background_tasks: FastAPI background tasks

    Returns:
        JSONResponse with status information
    """
    try:
        # Parse the request body
        payload = await request.json()
        
        # Log the event
        event_type = payload.get("event")
        logger.info(f"Received notification webhook event: {event_type}")
        
        # Handle different event types
        if event_type == "user.created":
            # Handle new user event
            await handle_new_user(payload, background_tasks)
        elif event_type == "subscription.changed":
            # Handle subscription change event
            await handle_subscription_change(payload, background_tasks)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            
        # Return success
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        logger.error(f"Error handling notification webhook: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)})

async def handle_new_user(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle a new user event.

    Args:
        payload: The event payload
        background_tasks: FastAPI background tasks
    """
    try:
        # Extract user data
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        if not email:
            logger.warning(f"No email in payload for user {user_id}")
            return
            
        # Get user details to check if they signed up with OAuth
        user = auth_service.get_user_by_id(user_id)
        is_oauth = False
        
        if user and user.get("identities"):
            for identity in user.get("identities", []):
                if identity.get("provider") != "email":
                    is_oauth = True
                    break
        
        # Send welcome email in the background
        background_tasks.add_task(
            email_service.send_welcome_email,
            email,
            is_oauth
        )
        
        logger.info(f"Queued welcome email for user {user_id} ({email})")
        
    except Exception as e:
        logger.error(f"Error handling new user notification: {str(e)}")

async def handle_subscription_change(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle a subscription change event.

    Args:
        payload: The event payload
        background_tasks: FastAPI background tasks
    """
    try:
        # Extract subscription data
        user_id = payload.get("user_id")
        old_data = payload.get("old_data")
        new_data = payload.get("new_data")
        
        if not user_id or not new_data:
            logger.warning("Missing required data in subscription change payload")
            return
            
        # Get user email
        user = auth_service.get_user_by_id(user_id)
        if not user or not user.get("email"):
            logger.warning(f"Could not find email for user {user_id}")
            return
            
        email = user.get("email")
        
        # Check for tier upgrade (free to premium)
        if not old_data:
            # New subscription
            tier = new_data.get("subscription_tier")
            if tier == "premium":
                # Send subscription confirmation email
                background_tasks.add_task(
                    email_service.send_subscription_confirmation_email,
                    email
                )
                logger.info(f"Queued subscription confirmation email for user {user_id} ({email})")
        else:
            # Existing subscription
            old_tier = old_data.get("subscription_tier")
            new_tier = new_data.get("subscription_tier")
            
            if old_tier != "premium" and new_tier == "premium":
                # User upgraded to premium
                background_tasks.add_task(
                    email_service.send_subscription_confirmation_email,
                    email
                )
                logger.info(f"Queued subscription upgrade email for user {user_id} ({email})")
                
            # Check for additional credits purchase
            old_credits = old_data.get("additional_credits_remaining", 0)
            new_credits = new_data.get("additional_credits_remaining", 0)
            
            if new_credits > old_credits:
                # User purchased additional credits
                credits_added = new_credits - old_credits
                background_tasks.add_task(
                    email_service.send_credits_confirmation_email,
                    email,
                    credits_added
                )
                logger.info(f"Queued credits confirmation email for user {user_id} ({email}) for {credits_added} credits")
                
    except Exception as e:
        logger.error(f"Error handling subscription change notification: {str(e)}")
