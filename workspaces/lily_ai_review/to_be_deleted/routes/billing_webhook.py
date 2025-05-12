"""
Stripe webhook handler for processing Stripe events.
This module provides a clean implementation of the Stripe webhook handler.
"""
import os
import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from app.services.billing.stripe_service_new import StripeService
from app.services.billing.subscription_service_clean import SubscriptionService
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/billing", tags=["billing"])

# Initialize services
supabase_client = get_supabase_client()
stripe_service = StripeService(supabase_client=supabase_client)
subscription_service = SubscriptionService()

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe, verifies their signature,
    and processes them accordingly.

    Args:
        request: The incoming request

    Returns:
        JSONResponse with status information
    """
    # Get the signature from the headers
    signature = request.headers.get("stripe-signature")

    # Read the request body
    payload = await request.body()

    # Verify the webhook signature
    try:
        event = stripe_service.handle_webhook(payload, signature)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe signature")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid payload")

    # Log the event type and details
    event_type = event.get("type")
    event_id = event.get("id")
    logger.info(f"Received Stripe webhook event: {event_type} (ID: {event_id})")

    # Log more details for debugging
    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        session_id = session.get("id")
        customer_id = session.get("customer")
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        mode = session.get("mode")
        subscription_id = session.get("subscription")
        logger.info(f"Checkout session details: ID={session_id}, Customer={customer_id}, User={user_id}, Mode={mode}, Subscription={subscription_id}")
    elif event_type == "customer.subscription.created" or event_type == "customer.subscription.updated":
        subscription = event.get("data", {}).get("object", {})
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        logger.info(f"Subscription details: ID={subscription_id}, Customer={customer_id}, User={user_id}, Status={status}")

    # Store the webhook event in the database for tracking purposes
    try:
        supabase_client.table("stripe_events").insert({
            "event_type": event_type,
            "event_id": event.get("id"),
            "data": event,
            "processed": False
        }).execute()
        logger.info(f"Stored webhook event in database: {event_type}")
    except Exception as db_error:
        logger.error(f"Error storing webhook event in database: {str(db_error)}")
        # Continue processing even if database storage fails

    # Handle different event types
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]

        # Get the user ID from the metadata
        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            logger.error("No user_id in session metadata")
            return JSONResponse({"status": "no user_id metadata"}, status_code=200)

        # Process the checkout session
        success = subscription_service.handle_checkout_session_completed(event["data"])

        if not success:
            logger.error(f"Failed to process checkout.session.completed for user {user_id}")
            return JSONResponse({"status": "error", "message": "Failed to process checkout session"}, status_code=200)

        logger.info(f"Successfully processed checkout.session.completed for user {user_id}")

    elif event_type == "customer.subscription.created":
        success = subscription_service.handle_subscription_created(event["data"])

        if not success:
            logger.error("Failed to process customer.subscription.created")
            return JSONResponse({"status": "error", "message": "Failed to process subscription created"}, status_code=200)

        logger.info("Successfully processed customer.subscription.created")

    elif event_type == "customer.subscription.updated":
        success = subscription_service.handle_subscription_updated(event["data"])

        if not success:
            logger.error("Failed to process customer.subscription.updated")
            return JSONResponse({"status": "error", "message": "Failed to process subscription updated"}, status_code=200)

        logger.info("Successfully processed customer.subscription.updated")

    elif event_type == "customer.subscription.deleted":
        success = subscription_service.handle_subscription_deleted(event["data"])

        if not success:
            logger.error("Failed to process customer.subscription.deleted")
            return JSONResponse({"status": "error", "message": "Failed to process subscription deleted"}, status_code=200)

        logger.info("Successfully processed customer.subscription.deleted")

    # Return success for any event type
    return JSONResponse({"status": "success"}, status_code=200)
