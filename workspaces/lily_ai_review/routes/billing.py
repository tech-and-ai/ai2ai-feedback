"""
Billing routes for the application.

This module provides routes for handling billing and subscription management.
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER, HTTP_400_BAD_REQUEST

from app.config import config
from app.logging import get_logger
from app.exceptions import PaymentError, ValidationError, AuthenticationError
from app.services.session_service import get_session_service
from app.services.billing.stripe_service import StripeService
from app.services.billing.subscription_service import SubscriptionService
from app.services.email.email_service import EmailService

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["billing"])

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Initialize services
session_service = get_session_service()
stripe_service = StripeService()
subscription_service = SubscriptionService()
email_service = EmailService()

@router.get("/subscription", response_class=HTMLResponse)
async def subscription_page(request: Request):
    """
    Render the subscription page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse: The subscription page
    """
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user = session_service.get_user(request)

    # Get user subscription
    subscription = subscription_service.get_user_subscription(user["id"])

    # Check if user is already a premium subscriber
    if subscription.get("subscription_tier") == "premium" and subscription.get("status") == "active":
        logger.info(f"Premium user {user['id']} accessing subscription page, redirecting to buy credits")
        return RedirectResponse(url="/billing/buy-credits", status_code=HTTP_303_SEE_OTHER)

    # Render the subscription page
    return templates.TemplateResponse(
        "subscription.html",
        {
            "request": request,
            "user": user,
            "subscription": subscription,
            "stripe_publishable_key": config.STRIPE_PUBLISHABLE_KEY
        }
    )

@router.get("/buy-credits", response_class=HTMLResponse)
async def buy_credits_page(request: Request):
    """
    Render the buy credits page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse: The buy credits page
    """
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user = session_service.get_user(request)

    # Get user subscription
    subscription = subscription_service.get_user_subscription(user["id"])

    # Verify subscription status with Stripe
    is_premium = subscription_service.verify_subscription_with_stripe(user["id"])

    # If verification failed, update the session data to reflect current subscription status
    if not is_premium:
        # Update session data
        session_service.update_user(request, {"subscription_tier": subscription.get("subscription_tier", "free")})

        # Check if user has additional credits
        additional_credits = subscription.get("additional_credits_remaining", 0)

        # Log the verification failure
        logger.warning(f"Subscription verification failed for user {user['id']}, redirecting to subscription")

        # Redirect with appropriate error message
        if additional_credits > 0:
            return RedirectResponse(url="/billing/subscription?error=subscription_required_for_credits", status_code=HTTP_303_SEE_OTHER)
        else:
            return RedirectResponse(url="/billing/subscription", status_code=HTTP_303_SEE_OTHER)

    # Render the buy credits page
    return templates.TemplateResponse(
        "buy_credits.html",
        {
            "request": request,
            "user": user,
            "subscription": subscription,
            "subscription_papers_remaining": subscription.get("papers_remaining", 0),
            "additional_papers_remaining": subscription.get("additional_credits_remaining", 0),
            "total_papers_remaining": subscription.get("total_papers_remaining", 0),
            "stripe_publishable_key": config.STRIPE_PUBLISHABLE_KEY
        }
    )

@router.get("/checkout/premium", response_class=JSONResponse)
async def create_premium_checkout(request: Request):
    """
    Create a checkout session for premium subscription.

    Args:
        request: The incoming request

    Returns:
        JSONResponse: The checkout session URL
    """
    try:
        # Check if user is logged in
        if not session_service.is_authenticated(request):
            logger.warning("User not authenticated, redirecting to login")
            return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

        # Get user data
        user = session_service.get_user(request)

        # Get price ID
        price_id = config.STRIPE_PREMIUM_PRICE_ID

        # Check if price ID is configured
        if not price_id:
            logger.error("Premium price ID not configured")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Premium price ID not configured"}
            )

        # Create success and cancel URLs
        success_url = f"{config.BASE_URL}/billing/subscription-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{config.BASE_URL}/billing/subscription"

        # Create metadata
        metadata = {
            "user_id": user["id"],
            "product_type": "premium_subscription"
        }

        # Create checkout session
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user["email"],
            metadata=metadata,
            mode="subscription"
        )

        # Return the checkout session URL
        return JSONResponse(content={"url": session.url})

    except PaymentError as e:
        # Log the error
        logger.error(f"Payment error creating premium checkout: {str(e)}")

        # Return error response
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": str(e)}
        )

    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error creating premium checkout: {str(e)}")

        # Return error response
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "An unexpected error occurred"}
        )

@router.get("/checkout/credits/{credits_type}", response_class=JSONResponse)
async def create_credits_checkout(request: Request, credits_type: str):
    """
    Create a checkout session for paper credits.

    Args:
        request: The incoming request
        credits_type: The type of credits to purchase (credits_5, credits_10, credits_25)

    Returns:
        JSONResponse: The checkout session URL
    """
    try:
        # Check if user is logged in
        if not session_service.is_authenticated(request):
            logger.warning("User not authenticated in create_credits_checkout, redirecting to login")
            return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

        # Get user data
        user = session_service.get_user(request)

        # Get user subscription
        subscription = subscription_service.get_user_subscription(user["id"])

        # Verify subscription status with Stripe
        is_premium = subscription_service.verify_subscription_with_stripe(user["id"])

        # If verification failed, update the session data to reflect current subscription status
        if not is_premium:
            # Update session data
            session_service.update_user(request, {"subscription_tier": subscription.get("subscription_tier", "free")})

            # Check if user has additional credits
            additional_credits = subscription.get("additional_credits_remaining", 0)

            # Log the verification failure
            logger.warning(f"Subscription verification failed for user {user['id']} in checkout/credits, redirecting to subscription")

            # Redirect with appropriate error message
            if additional_credits > 0:
                return JSONResponse(
                    status_code=HTTP_400_BAD_REQUEST,
                    content={"error": "Active premium subscription required to purchase credits", "redirect": "/billing/subscription?error=subscription_required_for_credits"}
                )
            else:
                return JSONResponse(
                    status_code=HTTP_400_BAD_REQUEST,
                    content={"error": "Active premium subscription required to purchase credits", "redirect": "/billing/subscription"}
                )

        # Validate credits type
        valid_credits_types = ["credits_5", "credits_10", "credits_25"]
        if credits_type not in valid_credits_types:
            logger.error(f"Invalid credits type: {credits_type}")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": "Invalid credits type"}
            )

        # Get price ID based on credits type
        price_id = None
        if credits_type == "credits_5":
            price_id = config.STRIPE_CREDITS_5_PRICE_ID
        elif credits_type == "credits_10":
            price_id = config.STRIPE_CREDITS_10_PRICE_ID
        elif credits_type == "credits_25":
            price_id = config.STRIPE_CREDITS_25_PRICE_ID

        # Check if price ID is configured
        if not price_id:
            logger.error(f"{credits_type} price ID not configured")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": f"{credits_type} price ID not configured"}
            )

        # Create success and cancel URLs
        success_url = f"{config.BASE_URL}/billing/credits-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{config.BASE_URL}/billing/buy-credits"

        # Create metadata
        metadata = {
            "user_id": user["id"],
            "product_type": "paper_credits",
            "credits_type": credits_type
        }

        # Create checkout session
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user["email"],
            metadata=metadata,
            mode="payment"
        )

        # Return the checkout session URL
        return JSONResponse(content={"url": session.url})

    except PaymentError as e:
        # Log the error
        logger.error(f"Payment error creating credits checkout: {str(e)}")

        # Return error response
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": str(e)}
        )

    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error creating credits checkout: {str(e)}")

        # Return error response
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "An unexpected error occurred"}
        )

@router.get("/subscription-success", response_class=HTMLResponse)
async def subscription_success(request: Request, session_id: str = None):
    """
    Handle successful subscription checkout.

    Args:
        request: The incoming request
        session_id: The checkout session ID

    Returns:
        HTMLResponse: The success page
    """
    try:
        # Check if user is logged in
        if not session_service.is_authenticated(request):
            logger.warning("User not authenticated in subscription-success, redirecting to login")
            return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

        # Get user data
        user = session_service.get_user(request)

        # Check if session ID is provided
        if not session_id:
            logger.error("No session ID provided for subscription success")
            return RedirectResponse(url="/billing/subscription?error=no_session_id", status_code=HTTP_303_SEE_OTHER)

        # Retrieve the checkout session
        session = stripe_service.retrieve_checkout_session(session_id)

        # Check if session is complete
        if session.get("status") != "complete":
            logger.error(f"Incomplete checkout session: {session_id}")
            return RedirectResponse(url="/billing/subscription?error=incomplete_session", status_code=HTTP_303_SEE_OTHER)

        # Get subscription ID
        subscription_id = session.get("subscription")

        # Check if subscription ID is provided
        if not subscription_id:
            logger.error(f"No subscription ID in session: {session_id}")
            return RedirectResponse(url="/billing/subscription?error=no_subscription_id", status_code=HTTP_303_SEE_OTHER)

        # Get subscription from Stripe
        subscription = stripe_service.get_subscription(subscription_id)

        # Check subscription status
        status = subscription.get("status")

        # Get subscription end date
        current_period_end = subscription.get("current_period_end")
        if current_period_end:
            from datetime import datetime
            end_date = datetime.fromtimestamp(current_period_end)
        else:
            from datetime import datetime, timedelta
            end_date = datetime.now() + timedelta(days=30)

        # Update user subscription
        updated_subscription = subscription_service.update_subscription(
            user_id=user["id"],
            tier="premium",
            status=status,
            papers_limit=10,  # Premium tier gets 10 papers per month
            stripe_subscription_id=subscription_id,
            stripe_customer_id=session.get("customer"),
            end_date=end_date
        )

        # Update session data with new subscription tier
        session_service.update_user(request, {"subscription_tier": "premium"})

        # Log the update
        logger.info(f"Updated subscription for user {user['id']} to premium tier and updated session data")

        # Redirect to dashboard with success message
        return RedirectResponse(url="/dashboard?subscription_success=true", status_code=HTTP_303_SEE_OTHER)

    except PaymentError as e:
        # Log the error
        logger.error(f"Payment error in subscription success: {str(e)}")

        # Redirect to subscription page with error
        return RedirectResponse(url=f"/billing/subscription?error={str(e)}", status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in subscription success: {str(e)}")

        # Redirect to subscription page with error
        return RedirectResponse(url="/billing/subscription?error=unexpected_error", status_code=HTTP_303_SEE_OTHER)

@router.get("/credits-success", response_class=HTMLResponse)
async def credits_success(request: Request, session_id: str = None):
    """
    Handle successful credits checkout.

    Args:
        request: The incoming request
        session_id: The checkout session ID

    Returns:
        HTMLResponse: The success page
    """
    try:
        # Check if user is logged in
        if not session_service.is_authenticated(request):
            logger.warning("User not authenticated in credits-success, redirecting to login")
            return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

        # Get user data
        user = session_service.get_user(request)

        # Check if session ID is provided
        if not session_id:
            logger.error("No session ID provided for credits success")
            return RedirectResponse(url="/billing/buy-credits?error=no_session_id", status_code=HTTP_303_SEE_OTHER)

        # Retrieve the checkout session
        session = stripe_service.retrieve_checkout_session(session_id)

        # Check if session is complete
        if session.get("status") != "complete":
            logger.error(f"Incomplete checkout session: {session_id}")
            return RedirectResponse(url="/billing/buy-credits?error=incomplete_session", status_code=HTTP_303_SEE_OTHER)

        # Get metadata
        metadata = session.get("metadata", {})
        credits_type = metadata.get("credits_type")

        # Determine credits amount based on credits type
        credits = 0
        if credits_type == "credits_5":
            credits = 5
        elif credits_type == "credits_10":
            credits = 10
        elif credits_type == "credits_25":
            credits = 25
        else:
            logger.error(f"Unknown credits type: {credits_type}")
            return RedirectResponse(url="/billing/buy-credits?error=unknown_credits_type", status_code=HTTP_303_SEE_OTHER)

        # Update user subscription with additional credits
        subscription_service.update_subscription(
            user_id=user["id"],
            additional_credits=credits,
            stripe_customer_id=session.get("customer")
        )

        # Log the update
        logger.info(f"Added {credits} credits for user {user['id']}")

        # Send confirmation email
        try:
            # Get user email from database
            from app.services.supabase_service import get_supabase_client
            supabase = get_supabase_client()
            result = supabase.from_("users_view").select("email").eq("id", user["id"]).execute()
            user_email = user.get("email")

            if result.data and len(result.data) > 0:
                user_email = result.data[0].get("email", user_email)

            if user_email:
                # Send email
                email_service.send_credits_confirmation_email(
                    email=user_email,
                    credit_count=credits
                )
                logger.info(f"Sent credits purchase confirmation email to {user_email}")
            else:
                logger.error(f"Could not find email for user {user['id']}")
        except Exception as email_error:
            # Log the error but continue
            logger.error(f"Error sending credits purchase confirmation email: {str(email_error)}")

        # Redirect to dashboard with success message
        return RedirectResponse(url=f"/dashboard?credits=success&amount={credits}", status_code=HTTP_303_SEE_OTHER)

    except PaymentError as e:
        # Log the error
        logger.error(f"Payment error in credits success: {str(e)}")

        # Redirect to buy credits page with error
        return RedirectResponse(url=f"/billing/buy-credits?error={str(e)}", status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in credits success: {str(e)}")

        # Redirect to buy credits page with error
        return RedirectResponse(url="/billing/buy-credits?error=unexpected_error", status_code=HTTP_303_SEE_OTHER)

@router.get("/manage", response_class=HTMLResponse)
async def manage_subscription(request: Request):
    """
    Render the subscription management page.

    Args:
        request: The incoming request

    Returns:
        HTMLResponse: The subscription management page
    """
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user = session_service.get_user(request)

    # Get user subscription
    subscription = subscription_service.get_user_subscription(user["id"])

    # Render the subscription management page
    return templates.TemplateResponse(
        "subscription_manage.html",
        {
            "request": request,
            "user": user,
            "subscription": subscription,
            "subscription_papers_remaining": subscription.get("papers_remaining", 0),
            "additional_papers_remaining": subscription.get("additional_credits_remaining", 0),
            "total_papers_remaining": subscription.get("total_papers_remaining", 0),
            "stripe_publishable_key": config.STRIPE_PUBLISHABLE_KEY
        }
    )
