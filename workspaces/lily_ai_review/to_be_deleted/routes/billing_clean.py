"""
Clean billing routes for handling Stripe checkout, webhooks, and subscription management.
"""
import os
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK, HTTP_404_NOT_FOUND
import logging

from app.services.billing.stripe_service_clean import StripeService
from app.services.billing.subscription_service_clean import SubscriptionService
from auth.dependencies import get_current_user
from app.utils.session_helpers import get_session_user, update_session_tier
from fastapi.templating import Jinja2Templates

# Configure logging
logger = logging.getLogger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize services
from app.utils.supabase_client import get_supabase_client
supabase_client = get_supabase_client()
stripe_service = StripeService(supabase_client=supabase_client)
subscription_service = SubscriptionService()

# Helper function to get the base URL
def get_base_url(request: Request = None) -> str:
    """
    Get the base URL for the application.
    
    Args:
        request: The request object (optional)
        
    Returns:
        Base URL as a string
    """
    # Use the BASE_URL environment variable if set
    base_url = os.getenv("BASE_URL")
    if base_url:
        return base_url
        
    # If request is provided, use host from request
    if request:
        host = request.headers.get("host", "localhost:8000")
        scheme = request.headers.get("x-forwarded-proto", "http")
        return f"{scheme}://{host}"
        
    # Default to localhost
    return "http://localhost:8000"

@router.get("/subscription")
async def subscription_page(request: Request, user=Depends(get_current_user)):
    """
    Render the subscription page.
    
    Args:
        request: The request object
        user: The authenticated user
        
    Returns:
        HTMLResponse with the subscription template
    """
    try:
        # Get user's subscription
        subscription = subscription_service.get_user_subscription(user.get("id"))
        
        # Get Stripe publishable key
        stripe_publishable_key = stripe_service.get_publishable_key()
        
        # Render the subscription page
        return templates.TemplateResponse(
            "billing/subscription.html",
            {
                "request": request,
                "user": user,
                "subscription": subscription,
                "stripe_publishable_key": stripe_publishable_key
            }
        )
    except Exception as e:
        logger.error(f"Error rendering subscription page: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while loading the subscription page"
        )

@router.get("/checkout")
async def create_checkout_session(request: Request, user=Depends(get_current_user)):
    """
    Create a checkout session for premium subscription.
    
    Args:
        request: The request object
        user: The authenticated user
        
    Returns:
        Redirect to the Stripe checkout page
    """
    try:
        # Get the base URL
        base_url = get_base_url(request)
        
        # Create success and cancel URLs
        success_url = f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/billing/cancel"
        
        # Get user's email
        user_email = user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )
            
        # Create checkout session
        session = subscription_service.create_checkout_session(
            user_id=user.get("id"),
            user_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Redirect to checkout page
        return RedirectResponse(url=session["url"])
        
    except ValueError as e:
        logger.error(f"Value error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.get("/success")
async def checkout_success(request: Request, session_id: str = None, background_tasks: BackgroundTasks = None):
    """
    Handle successful checkout.
    
    Args:
        request: The request object
        session_id: The Stripe session ID
        background_tasks: FastAPI background tasks
        
    Returns:
        Success page HTML or redirect
    """
    # Log request for debugging
    logger.info(f"Checkout success called with session_id: {session_id}")
    
    # Get user from session
    user = get_session_user(request)
    
    # If no session ID, redirect to dashboard with error
    if not session_id:
        logger.error("No session_id provided")
        return RedirectResponse(url="/dashboard?error=missing_session_id")
        
    try:
        # If user is not logged in
        if not user:
            # Try to get user email from session
            try:
                session = stripe_service.get_session(session_id)
                customer_email = session.get("customer_details", {}).get("email")
                if customer_email:
                    # Redirect to login with success message
                    return RedirectResponse(url=f"/auth/login?subscription_success=true&email={customer_email}")
            except Exception as e:
                logger.error(f"Error getting session details: {str(e)}")
                
            # Redirect to login page
            return RedirectResponse(url="/auth/login?subscription_pending=true")
            
        # Get session details from Stripe
        try:
            session = stripe_service.get_session(session_id)
            
            # Check if this is a subscription checkout
            if session.get("mode") == "subscription":
                # Immediately update session with premium tier
                update_session_tier(request, "premium")
                
                # Get user ID from session metadata or from current user
                user_id = session.get("metadata", {}).get("user_id", user.get("id"))
                
                # Update subscription in background to avoid blocking
                if background_tasks:
                    background_tasks.add_task(
                        subscription_service.handle_checkout_session_completed,
                        {'object': session}
                    )
                
                # Redirect to dashboard with success message
                return RedirectResponse(url="/dashboard?subscription_success=true")
            else:
                # Not a subscription checkout
                logger.warning(f"Checkout session {session_id} is not for a subscription")
                
            # Render success page with session details
            return templates.TemplateResponse(
                "billing/success.html",
                {
                    "request": request,
                    "user": user,
                    "session_id": session_id,
                    "session_details": session
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing checkout success: {str(e)}")
            
            # Update session anyway as a fallback
            update_session_tier(request, "premium")
            
            # Redirect to dashboard with success message
            return RedirectResponse(url="/dashboard?subscription_success=true")
            
    except Exception as e:
        logger.error(f"Error handling checkout success: {str(e)}")
        
        # Redirect to dashboard with error message
        return RedirectResponse(url="/dashboard?error=checkout_processing")

@router.get("/cancel")
async def checkout_canceled(request: Request):
    """
    Handle canceled checkout.
    
    Args:
        request: The request object
        
    Returns:
        Redirect to subscription page
    """
    return RedirectResponse(url="/billing/subscription?canceled=true")

@router.get("/manage")
async def manage_subscription(request: Request, user=Depends(get_current_user)):
    """
    Render the subscription management page.
    
    Args:
        request: The request object
        user: The authenticated user
        
    Returns:
        HTMLResponse with the manage subscription template
    """
    try:
        # Get user's subscription
        subscription = subscription_service.get_user_subscription(user.get("id"))
        
        # Render the manage subscription page
        return templates.TemplateResponse(
            "billing/manage.html",
            {
                "request": request,
                "user": user,
                "subscription": subscription
            }
        )
    except Exception as e:
        logger.error(f"Error rendering manage subscription page: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while loading the subscription management page"
        )

@router.get("/portal")
async def customer_portal(request: Request, user=Depends(get_current_user)):
    """
    Redirect to Stripe Customer Portal for subscription management.
    
    Args:
        request: The request object
        user: The authenticated user
        
    Returns:
        Redirect to Stripe Customer Portal
    """
    try:
        # Get base URL for return URL
        base_url = get_base_url(request)
        return_url = f"{base_url}/billing/manage"
        
        # Create customer portal session
        portal_session = subscription_service.create_customer_portal_session(
            user_id=user.get("id"),
            return_url=return_url
        )
        
        # Redirect to portal
        return RedirectResponse(url=portal_session["url"])
        
    except ValueError as e:
        logger.error(f"Value error creating portal session: {str(e)}")
        
        # Redirect back to manage page with error
        return RedirectResponse(url="/billing/manage?error=no_subscription")
        
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access customer portal"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks = None):
    """
    Handle Stripe webhook events.
    
    Args:
        request: The request object
        background_tasks: FastAPI background tasks
        
    Returns:
        JSON response with status
    """
    try:
        # Get the signature header
        signature = request.headers.get("stripe-signature")
        if not signature:
            logger.warning("Missing Stripe signature header")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Missing signature header"}
            )
            
        # Get the raw body
        body = await request.body()
        
        # Verify webhook signature and parse event
        try:
            event = stripe_service.handle_webhook(body, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Invalid signature"}
            )
            
        # Log event
        event_type = event.get("type")
        event_id = event.get("id")
        logger.info(f"Received Stripe webhook: {event_type} (ID: {event_id})")
        
        # Handle event in background if available
        if background_tasks:
            background_tasks.add_task(subscription_service.handle_webhook_event, event)
            logger.info(f"Added webhook event {event_id} to background tasks")
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={"status": "success", "message": "Webhook received and processing"}
            )
            
        # Otherwise handle synchronously
        result = subscription_service.handle_webhook_event(event)
        
        if result:
            return JSONResponse(
                status_code=HTTP_200_OK,
                content={"status": "success", "message": "Webhook processed successfully"}
            )
        else:
            logger.error(f"Error processing webhook event {event_id}")
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "Error processing webhook"}
            )
            
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Internal server error"}
        )

@router.get("/status")
async def subscription_status(request: Request, user=Depends(get_current_user)):
    """
    Get the current user's subscription status.
    
    Args:
        request: The request object
        user: The authenticated user
        
    Returns:
        JSON response with subscription status
    """
    try:
        # Get user's subscription
        subscription = subscription_service.get_user_subscription(user.get("id"))
        
        # Return subscription status
        return JSONResponse(
            status_code=HTTP_200_OK,
            content={
                "status": "success", 
                "subscription": {
                    "tier": subscription.get("subscription_tier"),
                    "is_active": subscription.get("is_active"),
                    "is_canceled": subscription.get("is_canceled"),
                    "is_expired": subscription.get("is_expired"),
                    "papers_limit": subscription.get("papers_limit"),
                    "papers_used": subscription.get("papers_used"),
                    "papers_remaining": subscription.get("papers_remaining")
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription status"
        ) 