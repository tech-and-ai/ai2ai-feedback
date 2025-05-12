"""
Stripe webhook handler for processing Stripe events.
"""
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST

from app.services.billing.stripe_service_simple import StripeService
from app.services.billing.subscription_service_simple import SubscriptionService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["billing"])

# Initialize services
stripe_service = StripeService()
subscription_service = SubscriptionService()

@router.post("/webhook", include_in_schema=True)
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

    # Log the signature for debugging
    logger.info(f"Received webhook with signature: {signature}")

    # Read the request body
    payload = await request.body()

    # Log the payload size for debugging
    logger.info(f"Webhook payload size: {len(payload)} bytes")

    # Verify the webhook signature
    try:
        # For debugging, log the first 100 characters of the payload
        logger.info(f"Webhook payload preview: {payload[:100]}")

        event = stripe_service.handle_webhook(payload, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook: {str(e)}")
        # Return a 200 response to acknowledge receipt even if verification fails
        # This prevents Stripe from retrying the webhook, which could cause duplicate processing
        return JSONResponse({"status": "error", "message": "Invalid webhook signature"})

    # Log the event type and details
    event_type = event.get("type")
    event_id = event.get("id")
    logger.info(f"Received Stripe webhook event: {event_type} (ID: {event_id})")

    # Handle different event types
    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})

        # Log session details
        session_id = session.get("id")
        customer_id = session.get("customer")
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        mode = session.get("mode")
        subscription_id = session.get("subscription")

        logger.info(f"Checkout session details: ID={session_id}, Customer={customer_id}, User={user_id}, Mode={mode}, Subscription={subscription_id}")

        # Process the checkout session
        success = subscription_service.handle_checkout_session_completed(session)

        if not success:
            logger.error(f"Failed to process checkout.session.completed for user {user_id}")
            # Return 200 to acknowledge receipt (don't retry)
            return JSONResponse({"status": "error", "message": "Failed to process checkout session"})

        logger.info(f"Successfully processed checkout.session.completed for user {user_id}")

    elif event_type == "customer.subscription.updated":
        subscription = event.get("data", {}).get("object", {})

        # Log subscription details
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status = subscription.get("status")

        logger.info(f"Subscription updated: ID={subscription_id}, Customer={customer_id}, Status={status}")

        # Find user by subscription ID
        try:
            response = subscription_service.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if response.data and len(response.data) > 0:
                user_id = response.data[0].get("user_id")

                # Update subscription status
                subscription_service.update_subscription(
                    user_id=user_id,
                    tier="premium",  # Keep the tier as premium
                    status=status
                )

                logger.info(f"Updated subscription status for user {user_id} to {status}")
            else:
                logger.error(f"No user found with subscription ID {subscription_id}")
        except Exception as e:
            logger.error(f"Error processing subscription.updated: {str(e)}")

    elif event_type == "customer.subscription.deleted":
        subscription = event.get("data", {}).get("object", {})

        # Log subscription details
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")

        logger.info(f"Subscription deleted: ID={subscription_id}, Customer={customer_id}")

        # Find user by subscription ID
        try:
            response = subscription_service.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if response.data and len(response.data) > 0:
                user_id = response.data[0].get("user_id")

                # Update subscription status
                subscription_service.update_subscription(
                    user_id=user_id,
                    tier="free",  # Downgrade to free tier
                    status="canceled",
                    papers_limit=1  # Reset to free tier limit
                )

                logger.info(f"Updated subscription for user {user_id} to free tier (canceled)")
            else:
                logger.error(f"No user found with subscription ID {subscription_id}")
        except Exception as e:
            logger.error(f"Error processing subscription.deleted: {str(e)}")

    # Return success for any event type
    return JSONResponse({"status": "success"})
