"""
Billing routes for handling Stripe checkout and subscription management.
"""
import stripe
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER

from app.config import config
from app.logging import get_logger
from app.exceptions import PaymentError, ValidationError, AuthenticationError
from app.services.session_service import get_session_service
from app.services.billing.stripe_service_simple import StripeService
from app.services.billing.subscription_service_simple import SubscriptionService

# Get logger
logger = get_logger(__name__)

# Initialize templates
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# Create router
router = APIRouter(tags=["billing"])

# Initialize services
session_service = get_session_service()
stripe_service = StripeService()
subscription_service = SubscriptionService()

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

@router.get("/subscription")
async def subscription_page(request: Request):
    """Render the subscription page."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")

    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user_id)

    # Check if user is already a premium subscriber
    if subscription.get("subscription_tier") == "premium" and subscription.get("status") == "active":
        logger.info(f"Premium user {user_id} accessing subscription page, redirecting to buy credits")
        return RedirectResponse(url="/billing/buy-credits", status_code=HTTP_303_SEE_OTHER)

    # Get Stripe publishable key
    stripe_publishable_key = stripe_service.get_publishable_key()

    # Get payment links from configuration
    payment_links = config.get_stripe_payment_links()
    stripe_payment_link_premium = payment_links["premium"]

    # Log the payment link for debugging
    logger.info(f"Using Stripe payment link: {stripe_payment_link_premium}")

    return templates.TemplateResponse(
        "subscription.html",
        {
            "request": request,
            "subscription": subscription,
            "stripe_publishable_key": stripe_publishable_key,
            "stripe_payment_link_premium": stripe_payment_link_premium
        }
    )

@router.get("/checkout/premium")
async def create_subscription_checkout(request: Request):
    """Create a checkout session for a premium subscription."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")
    user_email = request.session.get("email")

    logger.info(f"Processing checkout for user_id={user_id}, email={user_email}")

    # Create success and cancel URLs
    # Use the configured base URL
    base_url = config.BASE_URL

    # Log the base URL for debugging
    logger.info(f"Using base URL: {base_url}")

    success_url = f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/subscription?canceled=true"

    # Log the success and cancel URLs for debugging
    logger.info(f"Success URL: {success_url}")
    logger.info(f"Cancel URL: {cancel_url}")

    try:
        # Create checkout session
        session = stripe_service.create_checkout_session(
            customer_email=user_email,
            user_id=user_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        # Log the session URL for debugging
        logger.info(f"Redirecting to Stripe checkout: {session.url}")

        # Check if this is an AJAX request
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header:
            # Return JSON response with URL
            return JSONResponse(content={"url": session.url})
        else:
            # Redirect to checkout page
            return RedirectResponse(url=session.url, status_code=HTTP_303_SEE_OTHER)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise PaymentError(
            message="Failed to create checkout session",
            detail={"error": str(e)},
            payment_provider="stripe"
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return RedirectResponse(
            url="/subscription?error=checkout_failed",
            status_code=HTTP_303_SEE_OTHER
        )

@router.get("/checkout/credits/{credits_type}")
async def create_credits_checkout(credits_type: str, request: Request):
    """Create a checkout session for paper credits."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated in create_credits_checkout, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")
    user_email = request.session.get("email")
    subscription_tier = request.session.get("subscription_tier", "free")

    # Log session data for debugging
    logger.info(f"Credits checkout - Session data: user_id={user_id}, email={user_email}, subscription_tier={subscription_tier}")

    # Handle the case where the credits_type has a "credits_" prefix from the template
    if credits_type.startswith("credits_"):
        # Extract the number part (e.g., "credits_5" -> "5")
        amount = credits_type.split("_")[1]
        # Reconstruct the proper credits_type format
        credits_type = f"credits_{amount}"

    logger.info(f"Processing credits checkout for type: {credits_type}")

    # Validate credits type
    if credits_type not in ["credits_5", "credits_10", "credits_25"]:
        logger.error(f"Invalid credits type: {credits_type}")
        raise ValidationError(
            message=f"Invalid credits type: {credits_type}",
            detail={"credits_type": credits_type, "valid_types": ["credits_5", "credits_10", "credits_25"]}
        )

    # Create success and cancel URLs
    base_url = config.BASE_URL
    success_url = f"{base_url}/billing/credits-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/billing/buy-credits?canceled=true"

    logger.info(f"Success URL: {success_url}")
    logger.info(f"Cancel URL: {cancel_url}")

    try:
        # Create checkout session
        session = stripe_service.create_credits_checkout_session(
            credits_type=credits_type,
            customer_email=user_email,
            user_id=user_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        logger.info(f"Created checkout session with URL: {session.url}")

        # Redirect to checkout page
        return RedirectResponse(url=session.url, status_code=HTTP_303_SEE_OTHER)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating credits checkout session: {str(e)}")
        raise PaymentError(
            message="Failed to create credits checkout session",
            detail={"error": str(e), "credits_type": credits_type},
            payment_provider="stripe"
        )
    except Exception as e:
        logger.error(f"Error creating credits checkout session: {str(e)}")
        return RedirectResponse(
            url="/billing/buy-credits?error=checkout_failed",
            status_code=HTTP_303_SEE_OTHER
        )

@router.get("/success")
async def subscription_success(request: Request, session_id: str = None):
    """Handle successful subscription checkout."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated in subscription-success, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data from session
    user_id = request.session.get("user_id")
    user_email = request.session.get("email")

    # Log session data for debugging
    logger.info(f"Subscription success - Session data: user_id={user_id}, email={user_email}")

    # If session_id is provided, try to process it
    if session_id:
        try:
            # Get session details from Stripe
            session = stripe_service.get_session(session_id)
            logger.info(f"Retrieved Stripe subscription session: {session_id}")

            if session:
                # Log the session data for debugging
                logger.info(f"Subscription session data: {session}")
        except Exception as e:
            logger.error(f"Error processing subscription success: {str(e)}")

    # Update session with premium tier
    request.session["subscription_tier"] = "premium"
    logger.info(f"Updated session subscription_tier to premium for user {user_id}")

    # Redirect to dashboard with success message
    logger.info("Redirecting to dashboard with subscription_success=true")
    return RedirectResponse(
        url="/dashboard?subscription_success=true",
        status_code=HTTP_303_SEE_OTHER
    )

@router.get("/credits-success")
async def credits_success(request: Request, session_id: str = None):
    """Handle successful credits purchase."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated in credits-success, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data from session
    user_id = request.session.get("user_id")
    user_email = request.session.get("email")

    # Log session data for debugging
    logger.info(f"Credits success - Session data: user_id={user_id}, email={user_email}")

    # If session_id is provided, try to process it
    if session_id:
        try:
            # Get session details from Stripe
            session = stripe_service.get_session(session_id)
            logger.info(f"Retrieved Stripe session: {session_id}")

            if session:
                # Process the session
                metadata = session.get("metadata", {})
                stripe_user_id = metadata.get("user_id")
                credits = int(metadata.get("credits", 0))

                # Log the metadata for debugging
                logger.info(f"Session metadata: {metadata}")

                # Verify the user ID matches
                if stripe_user_id and stripe_user_id != user_id:
                    logger.warning(f"User ID mismatch: session={stripe_user_id}, request={user_id}")

                # Use the user ID from the session if available
                effective_user_id = user_id or stripe_user_id

                if effective_user_id and credits > 0:
                    # Add credits to user's account
                    success = subscription_service.add_paper_credits(effective_user_id, credits)
                    if success:
                        logger.info(f"Added {credits} credits to user {effective_user_id} from session {session_id}")
                    else:
                        logger.error(f"Failed to add credits to user {effective_user_id} from session {session_id}")
        except Exception as e:
            logger.error(f"Error processing credits success: {str(e)}")

    # Redirect to dashboard with success message
    logger.info("Redirecting to dashboard with credits_success=true")
    return RedirectResponse(
        url="/dashboard?credits_success=true",
        status_code=HTTP_303_SEE_OTHER
    )

@router.get("/manage")
async def manage_subscription(request: Request):
    """Manage a user's subscription."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")

    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user_id)

    # Check if user has a premium subscription
    if subscription.get("subscription_tier") != "premium":
        return RedirectResponse(url="/subscription", status_code=HTTP_303_SEE_OTHER)

    # Check if user has a Stripe customer ID
    customer_id = subscription.get("stripe_customer_id")
    if not customer_id:
        return RedirectResponse(
            url="/subscription?error=no_customer_id",
            status_code=HTTP_303_SEE_OTHER
        )

    # Create customer portal session
    try:
        base_url = config.BASE_URL
        portal_session = stripe_service.create_customer_portal_session(
            customer_id=customer_id,
            return_url=f"{base_url}/dashboard"
        )

        # Redirect to customer portal
        return RedirectResponse(url=portal_session.url, status_code=HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error creating customer portal session: {str(e)}")
        return RedirectResponse(
            url="/subscription?error=portal_failed",
            status_code=HTTP_303_SEE_OTHER
        )

@router.get("/buy-credits")
async def buy_credits_page(request: Request):
    """Render the buy credits page."""
    # Check if user is logged in
    if not session_service.is_authenticated(request):
        logger.warning("User not authenticated, redirecting to login")
        return RedirectResponse(url="/auth/login", status_code=HTTP_303_SEE_OTHER)

    # Get user data
    user_id = request.session.get("user_id")
    user_email = request.session.get("email")
    subscription_tier = request.session.get("subscription_tier", "free")

    # Log session data for debugging
    logger.info(f"Session data: user_id={user_id}, email={user_email}, subscription_tier={subscription_tier}")

    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user_id)

    # Log subscription data for debugging
    logger.info(f"Subscription data: {subscription}")

    # Get Stripe publishable key
    stripe_publishable_key = stripe_service.get_publishable_key()

    # Get payment links from configuration
    payment_links = config.get_stripe_payment_links()
    stripe_payment_link_credits_5 = payment_links["credits_5"]
    stripe_payment_link_credits_10 = payment_links["credits_10"]
    stripe_payment_link_credits_25 = payment_links["credits_25"]

    # Log the payment links for debugging
    logger.info(f"Using Stripe payment links: 5 credits: {stripe_payment_link_credits_5}, 10 credits: {stripe_payment_link_credits_10}, 25 credits: {stripe_payment_link_credits_25}")

    # Create a context with all necessary data
    context = {
        "request": request,
        "user": {
            "id": user_id,
            "email": user_email,
            "subscription_tier": subscription_tier
        },
        "subscription": subscription,
        "subscription_tier": subscription.get("subscription_tier", "free"),
        "subscription_papers_remaining": subscription.get("papers_remaining", 0),
        "additional_papers_remaining": subscription.get("additional_credits_remaining", 0),
        "total_papers_remaining": subscription.get("total_papers_remaining", 0),
        "stripe_publishable_key": stripe_publishable_key,
        "stripe_payment_link_credits_5": stripe_payment_link_credits_5,
        "stripe_payment_link_credits_10": stripe_payment_link_credits_10,
        "stripe_payment_link_credits_25": stripe_payment_link_credits_25
    }

    return templates.TemplateResponse("buy_credits.html", context)
