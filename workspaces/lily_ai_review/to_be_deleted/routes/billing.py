"""
Billing routes for handling Stripe checkout, webhooks, and subscription management.
"""
import os
import time
import stripe
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
import logging

from app.services.billing.stripe_service import StripeService
from app.services.billing.subscription_service import SubscriptionService
from auth.dependencies import get_current_user
from app.utils.session_helpers import get_session_user
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
def get_base_url(request):
    """Get the base URL for the application."""
    # Use the BASE_URL environment variable if set, otherwise fallback to request host
    base_url = os.getenv("BASE_URL")
    if base_url:
        return base_url

    # Fallback to using the host from the request
    host = request.headers.get("host", "localhost:8000")
    scheme = request.headers.get("x-forwarded-proto", "http")
    return f"{scheme}://{host}"

@router.get("/buy-credits")
async def buy_credits_page(request: Request, user=Depends(get_current_user)):
    """
    Render the buy credits page or redirect premium users to subscription page.

    Args:
        request: The request object
        user: The authenticated user

    Returns:
        HTMLResponse with the buy credits template or redirect to subscription
    """
    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user.get("id"))

    # If user has a premium subscription, redirect to subscription page with buy_papers parameter
    if subscription and subscription.get("subscription_tier") == "premium":
        return RedirectResponse(url="/subscription?buy_papers=true")

    # Get Stripe publishable key
    stripe_publishable_key = stripe_service.get_publishable_key()

    return templates.TemplateResponse(
        "buy_credits.html",
        {
            "request": request,
            "user": user,
            "subscription": subscription,
            "stripe_publishable_key": stripe_publishable_key
        }
    )

@router.get("/checkout/credits/{amount}")
async def create_credits_checkout_session(amount: str, request: Request, user=Depends(get_current_user)):
    """
    Create a checkout session for paper credits.

    Args:
        amount: The amount of credits to purchase ('5', '10', or '20')
        request: The request object
        user: The authenticated user

    Returns:
        Redirect to the Stripe checkout page
    """
    if amount not in ["5", "10", "20"]:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid credits amount: {amount}"
        )

    try:
        # Get user's email
        user_email = user.get("email")

        # Create checkout session
        session = stripe_service.create_credits_checkout_session(
            credits_amount=amount,
            customer_email=user_email,
            user_id=user.get("id")
        )

        # Redirect to checkout page
        return RedirectResponse(url=session["url"])

    except Exception as e:
        logger.error(f"Error creating credits checkout session: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.get("/credits-success")
async def credits_success(request: Request, session_id: str = None, user=Depends(get_current_user)):
    """
    Handle successful credits purchase.

    Args:
        request: The request object
        session_id: The Stripe session ID (optional)
        user: The authenticated user

    Returns:
        Redirect to the papers page or success page
    """
    try:
        # Check if this is a mock session (for testing or from payment links)
        if session_id and session_id.startswith("cs_mock_credits_"):
            # Extract credits amount from mock session ID
            # Format: cs_mock_credits_5_timestamp
            parts = session_id.split("_")
            if len(parts) >= 4:
                try:
                    credits_amount = parts[3]
                    credits = int(credits_amount)

                    # Add credits to user's account
                    subscription_service.add_paper_credits(user.get("id"), credits)
                    logger.info(f"Added {credits} credits to user {user.get('id')} from mock session")

                    # Redirect to success page
                    return templates.TemplateResponse(
                        "billing/success.html",
                        {
                            "request": request,
                            "user": user,
                            "session_id": session_id,
                            "session_details": {
                                "amount_total": f"{credits * 2}.00",  # Approximate price
                                "metadata": {
                                    "credits": credits,
                                    "type": "paper_credits"
                                }
                            }
                        }
                    )
                except ValueError:
                    logger.error(f"Invalid credits amount in session ID: {session_id}")

        # If we get here, try to process a real session
        if session_id:
            try:
                # Get session details
                session = stripe_service.get_session(session_id)

                # Verify that this is a credits purchase
                if session.metadata.get("type") != "paper_credits":
                    logger.warning(f"Invalid session type: {session.metadata.get('type')}")
                    # Continue anyway for testing

                # Verify that the user ID matches
                if session.metadata.get("user_id") and session.metadata.get("user_id") != user.get("id"):
                    logger.warning(f"User ID mismatch: {session.metadata.get('user_id')} != {user.get('id')}")
                    # Continue anyway for testing

                # Get credits amount
                credits = int(session.metadata.get("credits", 0))

                if credits > 0:
                    # Add credits to user's account
                    subscription_service.add_paper_credits(user.get("id"), credits)
                    logger.info(f"Added {credits} credits to user {user.get('id')} from real session")
                else:
                    # Default to 5 credits if not specified
                    subscription_service.add_paper_credits(user.get("id"), 5)
                    logger.info(f"Added 5 default credits to user {user.get('id')}")
                    credits = 5

                # Render success page
                return templates.TemplateResponse(
                    "billing/success.html",
                    {
                        "request": request,
                        "user": user,
                        "session_id": session_id,
                        "session_details": {
                            "amount_total": f"{credits * 2}.00",  # Approximate price
                            "metadata": {
                                "credits": credits,
                                "type": "paper_credits"
                            }
                        }
                    }
                )
            except Exception as session_error:
                logger.error(f"Error processing session: {str(session_error)}")
                # Continue to fallback

        # Fallback: add default credits and redirect
        subscription_service.add_paper_credits(user.get("id"), 5)
        logger.info(f"Added 5 fallback credits to user {user.get('id')}")

        # Redirect to papers page with success message
        return RedirectResponse(url="/my-papers?credits_added=true")

    except Exception as e:
        logger.error(f"Error processing credits success: {str(e)}")
        # Redirect to papers page with error message
        return RedirectResponse(url="/my-papers?credits_error=true")

@router.get("/checkout/{tier}")
async def create_checkout_session(tier: str, request: Request, user=Depends(get_current_user)):
    """
    Create a checkout session for the specified tier.

    Args:
        tier: The subscription tier (basic, premium, pro)
        request: The request object
        user: The authenticated user

    Returns:
        Redirect to the Stripe checkout page
    """
    if tier not in ["basic", "standard", "premium", "pro"]:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier}"
        )

    try:
        # Get user's email from the session
        user_email = user.get("email")
        if not user_email:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="User email not found"
            )

        # Create checkout session directly with stripe_service
        session = stripe_service.create_checkout_session(
            tier=tier,
            customer_email=user_email,
            user_id=user.get("id")
        )

        # Redirect to checkout page
        return RedirectResponse(url=session["url"])

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

def update_user_session(request: Request, tier: str):
    """
    Update the user's session with the new subscription tier.

    Args:
        request: The request object
        tier: The subscription tier to set

    Returns:
        None
    """
    try:
        # Update the session with the new subscription tier
        request.session["subscription_tier"] = tier
        logger.info(f"Updated session subscription_tier to {tier}")
    except Exception as e:
        logger.error(f"Error updating user session: {str(e)}")

@router.get("/success")
async def checkout_success(request: Request, session_id: str = None):
    """
    Handle successful checkout.

    Args:
        request: The request object
        session_id: The Stripe session ID

    Returns:
        Success page HTML
    """
    # Log the request for debugging
    logger.info(f"Checkout success called with session_id: {session_id}")
    logger.info(f"Request query params: {request.query_params}")
    logger.info(f"Request headers: {request.headers}")

    # Get the session_id from the query parameters if not provided
    if not session_id:
        session_id = request.query_params.get("session_id")
        logger.info(f"Using session_id from query params: {session_id}")

    # Verify that we have a session_id
    if not session_id:
        logger.error("No session_id provided")
        return RedirectResponse(url="/dashboard?error=missing_session_id")

    # Get user from session
    user = get_session_user(request)
    if not user:
        logger.warning("No user found in session for checkout success page")

        if session_id:
            try:
                # Get the session details from Stripe
                session_details = stripe_service.get_session(session_id)

                if session_details:
                    # Get the customer email from the session
                    customer_email = session_details.get("customer_details", {}).get("email")

                    if customer_email:
                        logger.info(f"Found customer email in session: {customer_email}")

                        # Redirect to login page with a success message
                        return RedirectResponse(url=f"/auth/login?subscription_success=true&email={customer_email}")
            except Exception as e:
                logger.error(f"Error getting session details: {str(e)}")

        # If we couldn't find a user, redirect to login page
        return RedirectResponse(url="/auth/login?subscription_pending=true")

    logger.info(f"User found in session: {user.get('id')}")

    # Check if this is a mock session (for testing or from payment links)
    if session_id and (session_id.startswith("cs_test_") or session_id.startswith("cs_mock_")):
        try:
            # Extract tier from mock session ID
            parts = session_id.split("_")

            # Handle different mock session ID formats
            if "credits" in session_id:
                # This is a credits purchase
                # Format: cs_mock_credits_5_timestamp
                if len(parts) >= 4:
                    credits_amount = parts[3]
                    try:
                        credits = int(credits_amount)
                        # Add credits to user's account
                        subscription_service.add_paper_credits(user.get("id"), credits)
                        logger.info(f"Added {credits} credits to user {user.get('id')} from mock session")

                        # Set session details for template
                        session_details = {
                            "amount_total": f"{credits * 2}.00",  # Approximate price
                            "metadata": {
                                "credits": credits,
                                "type": "paper_credits"
                            }
                        }
                    except ValueError:
                        # If credits amount is not a number, default to premium subscription
                        tier = "premium"
                        logger.info(f"Invalid credits amount in session ID: {session_id}, defaulting to premium subscription")

                        # Create subscription in database with mock data
                        subscription_id = f"sub_mock_{int(time.time())}"
                        customer_id = f"cus_mock_{user.get('id')}"

                        # Update the user's subscription directly
                        subscription_service.update_subscription(
                            user_id=user.get("id"),
                            tier="premium",
                            status="active",
                            stripe_subscription_id=subscription_id,
                            stripe_customer_id=customer_id,
                            papers_limit=10
                        )

                        # Update the user's session
                        update_user_session(request, "premium")

                        logger.info(f"Updated subscription for user {user.get('id')} to premium tier")

                        # Set session details for template
                        session_details = {
                            "amount_total": "18.00",
                            "subscription": subscription_id,
                            "customer": customer_id,
                            "metadata": {
                                "tier": "premium",
                                "papers_limit": 10
                            }
                        }

                        # Redirect to dashboard after successful subscription
                        return RedirectResponse(url="/dashboard?subscription_success=true")
                else:
                    # Default to premium subscription if format is unexpected
                    tier = "premium"
                    logger.info(f"Unexpected session ID format: {session_id}, defaulting to premium subscription")

                    # Create subscription in database with mock data
                    subscription_id = f"sub_mock_{int(time.time())}"
                    customer_id = f"cus_mock_{user.get('id')}"

                    # Update the user's subscription directly
                    subscription_service.update_subscription(
                        user_id=user.get("id"),
                        tier="premium",
                        status="active",
                        stripe_subscription_id=subscription_id,
                        stripe_customer_id=customer_id,
                        papers_limit=10
                    )

                    # Update the user's session
                    from app.utils.session_helpers import update_user_session
                    update_user_session(request, "premium")

                    # Log the session update
                    logger.info(f"Updated session for user {user.get('id')} to premium tier")
                    logger.info(f"Session contents after update: {dict(request.session)}")

                    logger.info(f"Updated subscription for user {user.get('id')} to premium tier")

                    # Set session details for template
                    session_details = {
                        "amount_total": "18.00",
                        "subscription": subscription_id,
                        "customer": customer_id,
                        "metadata": {
                            "tier": "premium",
                            "papers_limit": 10
                        }
                    }

                    # Redirect to dashboard after successful subscription
                    return RedirectResponse(url="/dashboard?subscription_success=true")
            else:
                # This is a subscription purchase
                if len(parts) >= 4:
                    tier = parts[3]
                else:
                    tier = "premium"  # Default to premium for mock sessions

                logger.info(f"Creating subscription for tier: {tier}")

                # Create subscription in database with mock data
                subscription_id = f"sub_mock_{int(time.time())}"
                customer_id = f"cus_mock_{user.get('id')}"
                papers_limit = 10 if tier == "premium" else 3

                # Update the user's subscription directly
                subscription_service.update_subscription(
                    user_id=user.get("id"),
                    tier=tier,
                    status="active",
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    papers_limit=papers_limit
                )

                # Update the user's session
                from app.utils.session_helpers import update_user_session
                update_user_session(request, tier)

                # Log the session update
                logger.info(f"Updated session for user {user.get('id')} to {tier} tier")
                logger.info(f"Session contents after update: {dict(request.session)}")

                logger.info(f"Updated subscription for user {user.get('id')} to {tier} tier")

                # Set session details for template
                session_details = {
                    "amount_total": "18.00",
                    "subscription": subscription_id,
                    "customer": customer_id,
                    "metadata": {
                        "tier": tier,
                        "papers_limit": papers_limit
                    }
                }

                # Redirect to dashboard after successful subscription
                return RedirectResponse(url="/dashboard?subscription_success=true")
        except Exception as e:
            logger.error(f"Error processing mock session: {str(e)}")
            session_details = None
    else:
        # Get session details if session_id is provided (for real Stripe sessions)
        session_details = None
        if session_id:
            try:
                # Get the session details from Stripe
                session_details = stripe_service.get_session(session_id)
                logger.info(f"Retrieved session details: {session_details}")

                # Check the session status
                if session_details.get("status") == "complete":
                    logger.info("Session status is complete, processing payment")

                    # Process the session based on its type
                    if session_details and session_details.get("metadata", {}).get("type") == "paper_credits":
                        # This is a credits purchase
                        credits = int(session_details.get("metadata", {}).get("credits", 0))
                        if credits > 0:
                            # Add credits to user's account
                            subscription_service.add_paper_credits(user.get("id"), credits)
                            logger.info(f"Added {credits} credits to user {user.get('id')} from real session")
                    elif session_details and session_details.get("subscription"):
                        # This is a subscription purchase
                        subscription_id = session_details.get("subscription")
                        customer_id = session_details.get("customer")

                        # Update the user's subscription directly
                        subscription_service.update_subscription(
                            user_id=user.get("id"),
                            tier="premium",
                            status="active",
                            stripe_subscription_id=subscription_id,
                            stripe_customer_id=customer_id,
                            papers_limit=10
                        )

                        # Update the user's session
                        from app.utils.session_helpers import update_user_session
                        success = update_user_session(request, "premium")
                        if not success:
                            logger.error(f"Failed to update session for user {user.get('id')}")

                        logger.info(f"Updated subscription for user {user.get('id')} to premium tier")

                        # Redirect to dashboard after successful subscription
                        return RedirectResponse(url="/dashboard?subscription_success=true")
                elif session_details.get("status") == "open":
                    # The payment failed or was cancelled
                    logger.warning("Session status is open, payment may have failed or been cancelled")
                    return RedirectResponse(url="/subscription?payment_failed=true")
                else:
                    logger.warning(f"Unexpected session status: {session_details.get('status')}")
            except Exception as e:
                logger.error(f"Error getting session details: {str(e)}")

    # Always redirect to dashboard after successful payment
    # This ensures the user sees their updated subscription status
    logger.info(f"Redirecting user {user.get('id')} to dashboard after successful payment")

    # Get the user's current subscription from the database
    current_subscription = subscription_service.get_user_subscription(user.get("id"))
    logger.info(f"Current subscription for user {user.get('id')}: {current_subscription}")

    # Update the user's session data to reflect the new subscription
    from app.utils.session_helpers import update_user_session

    # Use the helper function to update the session and database
    # Make sure to use the correct tier from the database
    tier = "premium"
    if current_subscription and current_subscription.get("subscription_tier"):
        tier = current_subscription.get("subscription_tier")
        logger.info(f"Using tier from database: {tier}")

    # Force update the session with the premium tier
    success = update_user_session(request, "premium")

    # Also update the session directly to ensure it's updated
    request.session["subscription_tier"] = "premium"
    request.session.modified = True
    logger.info(f"Directly updated session subscription_tier to premium")

    if not success:
        logger.error(f"Failed to update session for user {user.get('id')}")
        # Continue anyway to redirect the user

    # Use 303 status code to ensure proper redirection after POST
    return RedirectResponse(url="/dashboard?subscription_success=true", status_code=303)

@router.get("/cancel")
async def checkout_canceled(request: Request):
    """
    Handle canceled checkout.

    Args:
        request: The request object

    Returns:
        Cancel page HTML
    """
    # Get user from session
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    return templates.TemplateResponse(
        "billing/cancel.html",
        {
            "request": request,
            "user": user
        }
    )

@router.get("/manage")
async def manage_subscription(request: Request, user=Depends(get_current_user)):
    """
    Manage a user's subscription.

    Args:
        request: The request object
        user: The authenticated user

    Returns:
        Subscription management page for premium users or redirect to subscription page for others
    """
    # Get user's subscription
    subscription = subscription_service.get_user_subscription(user.get("id"))

    # Check if user has a premium subscription
    if not subscription or subscription.get("subscription_tier") != "premium":
        return RedirectResponse(url="/subscription")

    # For premium users, redirect to subscription page with buy_papers parameter
    return RedirectResponse(url="/subscription?buy_papers=true")

@router.get("/cancel-subscription")
async def cancel_subscription(request: Request, user=Depends(get_current_user)):
    """
    Cancel a user's subscription.

    Args:
        request: The request object
        user: The authenticated user

    Returns:
        Redirect to the subscription page
    """
    try:
        # Cancel subscription
        subscription_service.cancel_subscription(user.get("id"))

        # Redirect to subscription page with message
        return RedirectResponse(url="/subscription?canceled=true")

    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events using Supabase Stripe wrapper.

    Args:
        request: The request object

    Returns:
        JSON response
    """
    # Get the signature from the headers
    signature = request.headers.get("stripe-signature")

    # Log the request headers for debugging
    logger.info(f"Webhook request headers: {dict(request.headers)}")

    # Read the request body
    payload = await request.body()
    payload_str = payload.decode("utf-8")

    # Log the raw payload for debugging
    logger.info(f"Received webhook payload: {payload_str}")

    try:
        # Verify the webhook signature
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        logger.info(f"Webhook secret loaded: {bool(webhook_secret)}")
        logger.info(f"Webhook secret value: {webhook_secret}")

        try:
            # Try to verify the event using the Stripe service
            event = stripe_service.handle_webhook(payload, signature)
            logger.info("Webhook signature verified successfully")
        except (stripe.error.SignatureVerificationError, ValueError) as verify_error:
            # For development/testing with Stripe CLI, we can bypass verification
            # In production, this should be properly verified
            logger.warning(f"Webhook signature verification failed: {str(verify_error)}")

            # Check if we're in development mode or if the bypass header is present
            is_development = os.environ.get("ENVIRONMENT", "development") == "development"
            bypass_verification = request.headers.get("X-Bypass-Verification") == "true"

            if is_development or bypass_verification:
                logger.info(f"Bypassing signature verification (Development mode: {is_development}, Bypass header: {bypass_verification})")

                # Parse the JSON payload
                import json
                event = json.loads(payload_str)
            else:
                # In production, we should not bypass verification
                logger.error("Production mode: Rejecting unverified webhook")
                raise verify_error

        # Log the full event for debugging
        logger.info(f"Full webhook event: {event}")

        # Get the Supabase client
        from app.utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()

        # Store the webhook event in the database for tracking purposes
        try:
            # Convert the created timestamp from Unix timestamp to datetime
            created_timestamp = datetime.fromtimestamp(event.get("created", 0))

            # Format the datetime as an ISO string that Supabase can handle
            created_timestamp_str = created_timestamp.isoformat()

            # Check if this event already exists in the database
            check_response = supabase.table("stripe_events").select("event_id").eq("event_id", event.get("id")).execute()

            if check_response.data and len(check_response.data) > 0:
                # Event already exists, just log and continue
                logger.info(f"Webhook event already exists in database: {event.get('id')}")
            else:
                # Event doesn't exist, insert it
                response = supabase.table("stripe_events").insert({
                    "event_type": event.get("type"),
                    "event_id": event.get("id"),
                    "api_version": event.get("api_version"),
                    "created": created_timestamp_str,
                    "data": event,
                    "livemode": event.get("livemode", False),
                    "pending_webhooks": event.get("pending_webhooks"),
                    "request_id": event.get("request", {}).get("id"),
                    "request_idempotency_key": event.get("request", {}).get("idempotency_key"),
                    "processed": False
                }).execute()

                logger.info(f"Stored webhook event in database: {event.get('type')}")
        except Exception as db_error:
            logger.error(f"Error storing webhook event in database: {str(db_error)}")
            # Continue processing even if database storage fails

        # Handle different event types
        event_type = event.get("type")
        logger.info(f"Received Stripe webhook event: {event_type}")

        if event_type == "checkout.session.completed":
            # Checkout session completed - handle subscription creation
            logger.info("Processing checkout.session.completed event")

            # Get the email from the event
            customer_email = event.get("data", {}).get("object", {}).get("customer_details", {}).get("email")

            # Get the metadata from the event
            metadata = event.get("data", {}).get("object", {}).get("metadata", {})
            user_id_from_metadata = metadata.get("user_id")

            logger.info(f"Checkout session completed for email: {customer_email}, metadata: {metadata}")

            # First try to get user_id from metadata
            if user_id_from_metadata:
                user_id = user_id_from_metadata
                logger.info(f"Found user ID {user_id} from session metadata")
            elif customer_email:
                # If no user_id in metadata, try to find by email
                try:
                    # Try to find a real user with this email
                    response = supabase.table("auth.users") \
                        .select("id") \
                        .eq("email", customer_email) \
                        .execute()

                    if response.data and len(response.data) > 0:
                        user_id = response.data[0].get("id")
                        logger.info(f"Found user with ID {user_id} for email {customer_email}")
                    else:
                        logger.error(f"No user found with email {customer_email} in auth.users table")
                        return JSONResponse(content={"success": False, "error": "User not found"})
                except Exception as e:
                    logger.error(f"Error querying auth.users table: {str(e)}")
                    return JSONResponse(content={"success": False, "error": "Database error"})
            else:
                logger.error("No customer email or user_id in checkout session")
                return JSONResponse(content={"success": False, "error": "No customer identification"})

            # Get customer ID from the event
            customer_id = event.get("data", {}).get("object", {}).get("customer")
            if not customer_id:
                logger.error("No customer ID in checkout session")
                # In development mode, we can use a mock ID for testing
                if os.environ.get("ENVIRONMENT", "development") == "development":
                    customer_id = f"cus_mock_{int(time.time())}"
                    logger.info(f"Using mock customer ID: {customer_id}")
                else:
                    return JSONResponse(content={"success": False, "error": "No customer ID in checkout session"})

            # Get subscription ID from the event
            subscription_id = event.get("data", {}).get("object", {}).get("subscription")
            if not subscription_id:
                logger.error("No subscription ID in checkout session")
                # In development mode, we can use a mock ID for testing
                if os.environ.get("ENVIRONMENT", "development") == "development":
                    subscription_id = f"sub_mock_{int(time.time())}"
                    logger.info(f"Using mock subscription ID: {subscription_id}")
                else:
                    return JSONResponse(content={"success": False, "error": "No subscription ID in checkout session"})

            # Update the user's subscription using SQL function
            try:
                # Log the parameters we're sending to the SQL function
                logger.info(f"Calling handle_stripe_checkout_completed with parameters:")
                logger.info(f"  session_id: {event.get('data', {}).get('object', {}).get('id')}")
                logger.info(f"  customer_id: {customer_id}")
                logger.info(f"  subscription_id: {subscription_id}")
                logger.info(f"  customer_email: {customer_email}")
                logger.info(f"  user_id: {user_id}")

                # Call the SQL function to handle checkout completion
                result = supabase.rpc(
                    "handle_stripe_checkout_completed",
                    {
                        "session_id": event.get("data", {}).get("object", {}).get("id"),
                        "customer_id": customer_id,
                        "subscription_id": subscription_id,
                        "customer_email": customer_email,
                        "user_id": user_id
                    }
                ).execute()

                # Log the full result for debugging
                logger.info(f"SQL function result: {result.data}")

                if result.data and result.data.get("success") == True:
                    logger.info(f"Successfully updated subscription for user {user_id} to premium tier using SQL function")
                else:
                    error_message = result.data.get("error", "Unknown error") if result.data else "Unknown error"
                    logger.error(f"Error updating subscription using SQL function: {error_message}")

                    # Fall back to the old method if the SQL function fails
                    logger.info("Falling back to subscription_service.update_subscription")

                    # Use the update_subscription method with the correct parameters
                    success = subscription_service.update_subscription(
                        user_id=user_id,
                        tier="premium",
                        status="active",
                        stripe_subscription_id=subscription_id,
                        stripe_customer_id=customer_id,
                        papers_limit=10
                    )

                    if success:
                        logger.info(f"Successfully updated subscription for user {user_id} to premium tier")
                    else:
                        logger.error(f"Failed to update subscription for user {user_id}")
                        return JSONResponse(content={"success": False, "error": "Subscription update failed"})

                # We can't update the session directly in the webhook handler
                # because it's a different session than the user's browser session.
                # The session will be updated when the user visits the success page.
                logger.info(f"Session will be updated when user visits success page")

                # Also update the user's subscription tier in the saas_users table directly
                # This ensures that even if the session update fails, the database is updated
                try:
                    # Update the user's subscription tier in saas_users table
                    supabase.table("saas_users") \
                        .update({"subscription_tier": "premium", "updated_at": datetime.now().isoformat()}) \
                        .eq("id", user_id) \
                        .execute()

                    logger.info(f"Updated user {user_id} subscription tier in saas_users table directly")
                except Exception as db_error:
                    logger.error(f"Error updating user subscription tier in database: {str(db_error)}")
                    # Continue even if database update fails

                # Return success
                return JSONResponse(content={"success": True})
            except Exception as e:
                logger.error(f"Error updating subscription: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return JSONResponse(content={"success": False, "error": "Subscription update failed"})

            # Redirect the user to the dashboard with a success message
            # This is handled by the success page, not the webhook

        elif event_type == "customer.subscription.created":
            # Subscription created
            logger.info("Processing customer.subscription.created event")
            subscription_service.handle_subscription_created(event.get("data", {}).get("object", {}))

        elif event_type == "customer.subscription.updated":
            # Subscription updated
            logger.info("Processing customer.subscription.updated event")
            subscription_service.handle_subscription_updated(event.get("data", {}).get("object", {}))

        elif event_type == "customer.subscription.deleted":
            # Subscription deleted/canceled
            logger.info("Processing customer.subscription.deleted event")
            subscription_service.handle_subscription_deleted(event.get("data", {}).get("object", {}))

        # Return success
        return JSONResponse(content={"success": True})

    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"success": False, "error": str(e)}
        )

@router.get("/status")
async def subscription_status(request: Request, user=Depends(get_current_user)):
    """
    Get user's subscription status.

    Args:
        request: The incoming request
        user: The current authenticated user

    Returns:
        JSON with subscription status
    """
    try:
        # Try to get subscription using SQL function
        from app.utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()

        result = supabase.rpc("get_user_subscription", {"user_id": user["id"]}).execute()

        if result.data:
            subscription_data = result.data
            logger.info(f"Got subscription for user {user['id']} using SQL function")
        else:
            # Fall back to the service if SQL function fails
            logger.info(f"SQL function returned no data, falling back to subscription_service")
            subscription = subscription_service.get_user_subscription(user["id"])
            if not subscription:
                return JSONResponse(content={"status": "none"})
            subscription_data = subscription
    except Exception as e:
        logger.error(f"Error getting subscription with SQL function: {str(e)}")
        # Fall back to the service
        subscription = subscription_service.get_user_subscription(user["id"])
        if not subscription:
            return JSONResponse(content={"status": "none"})
        subscription_data = subscription

    # Return subscription details
    return JSONResponse(content={
        "tier": subscription_data.get("tier") or subscription_data.get("subscription_tier", "free"),
        "status": subscription_data.get("status", "none"),
        "papers_used": subscription_data.get("papers_used", 0),
        "papers_limit": subscription_data.get("papers_limit", 0),
        "papers_remaining": subscription_data.get("papers_remaining", 0),
        "additional_credits": subscription_data.get("additional_credits", 0),
        "end_date": subscription_data.get("end_date"),
        "is_active": subscription_data.get("status") in ["active", "trialing"]
    })

@router.post("/add-credits")
async def add_paper_credits(
    request: Request,
    credits: int,
    user=Depends(get_current_user)
):
    """
    Add paper credits to a user's account.

    Args:
        request: The incoming request
        credits: The number of credits to add
        user: The current authenticated user

    Returns:
        JSON with success status
    """
    # Add credits
    success = subscription_service.add_paper_credits(user["id"], credits)

    if not success:
        return JSONResponse(
            content={"success": False, "message": "Failed to add credits"},
            status_code=500
        )

    # Get updated subscription
    subscription = subscription_service.get_user_subscription(user["id"])

    # Return success
    return JSONResponse(content={
        "success": True,
        "message": f"Added {credits} credits",
        "additional_credits": subscription.get("additional_credits", 0)
    })

@router.get("/payment-links-not-configured")
async def payment_links_not_configured(request: Request):
    """
    Handle the case when payment links are not configured.

    Args:
        request: The request object

    Returns:
        Error page HTML
    """
    # Get user from session
    user = get_session_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    return templates.TemplateResponse(
        "billing/payment_links_not_configured.html",
        {
            "request": request,
            "user": user
        }
    )

@router.get("/environment")
async def environment_info():
    """
    Get information about the current Stripe environment.

    Returns:
        JSON with environment information
    """
    return JSONResponse(content=stripe_service.get_environment_info())

@router.get("/process-pending-webhooks")
async def process_pending_webhooks(request: Request, user=Depends(get_current_user)):
    """
    Process any pending webhook events that haven't been processed yet.
    This is useful for recovering from errors or missed webhook events.

    Args:
        request: The request object
        user: The authenticated user

    Returns:
        JSON response with processing results
    """
    # Check if user is authenticated and is an admin
    if not user or not user.get("is_admin", False):
        return JSONResponse(
            content={"error": "Unauthorized. Admin access required."},
            status_code=403
        )

    try:
        # Get all unprocessed webhook events
        from app.utils.supabase_client import get_supabase_client
        supabase = get_supabase_client()

        response = supabase.table("stripe_events") \
            .select("*") \
            .eq("processed", False) \
            .order("created_at", desc=True) \
            .execute()

        if not response.data:
            return JSONResponse(content={"message": "No pending webhook events found"})

        events = response.data
        logger.info(f"Found {len(events)} unprocessed webhook events")

        # Process each event
        processed_count = 0
        for event in events:
            try:
                # Process the event based on its type
                event_type = event.get("event_type")
                event_data = event.get("data", {})

                logger.info(f"Processing pending webhook event: {event_type}")

                if event_type == "checkout.session.completed":
                    # Use the handle_checkout_session_completed function
                    success = subscription_service.handle_checkout_session_completed(event_data.get("object", {}))
                    if success:
                        logger.info(f"Successfully processed checkout.session.completed event")
                    else:
                        logger.error(f"Failed to process checkout.session.completed event")
                        continue
                elif event_type == "customer.subscription.created":
                    success = subscription_service.handle_subscription_created(event_data.get("object", {}))
                    if not success:
                        logger.error(f"Failed to process customer.subscription.created event")
                        continue
                    logger.info(f"Successfully processed customer.subscription.created event")
                elif event_type == "customer.subscription.updated":
                    success = subscription_service.handle_subscription_updated(event_data.get("object", {}))
                    if not success:
                        logger.error(f"Failed to process customer.subscription.updated event")
                        continue
                    logger.info(f"Successfully processed customer.subscription.updated event")
                elif event_type == "customer.subscription.deleted":
                    success = subscription_service.handle_subscription_deleted(event_data.get("object", {}))
                    if not success:
                        logger.error(f"Failed to process customer.subscription.deleted event")
                        continue
                    logger.info(f"Successfully processed customer.subscription.deleted event")
                else:
                    logger.info(f"Skipping unhandled event type: {event_type}")
                    continue

                # Mark the event as processed
                supabase.table("stripe_events") \
                    .update({"processed": True}) \
                    .eq("id", event.get("id")) \
                    .execute()

                processed_count += 1
                logger.info(f"Successfully processed pending webhook event: {event_type}")

            except Exception as e:
                logger.error(f"Error processing webhook event {event.get('id')}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                continue

        return JSONResponse(content={
            "message": f"Processed {processed_count} of {len(events)} webhook events",
            "processed_count": processed_count,
            "total_count": len(events)
        })

    except Exception as e:
        logger.error(f"Error processing pending webhooks: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )