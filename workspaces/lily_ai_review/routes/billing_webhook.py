"""
Stripe webhook handler for processing Stripe events.
"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import config
from app.logging import get_logger
from app.services.billing.stripe_service import StripeService
from app.services.billing.subscription_service import SubscriptionService
from app.services.session_service import get_session_service
from app.services.email.email_service import EmailService

# Configure logger
logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["billing"])

# Initialize services
stripe_service = StripeService()
subscription_service = SubscriptionService()
session_service = get_session_service()
email_service = EmailService()

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

        # Always verify webhook signatures in production for security
        try:
            # Attempt to verify the signature
            event = stripe_service.handle_webhook(payload, signature)
            logger.info("Webhook signature verified successfully")
        except Exception as sig_error:
            # Log the error but continue processing in development mode only
            if config.ENV == "development":
                logger.warning(f"Webhook signature verification failed, but continuing in development mode: {str(sig_error)}")
                event = json.loads(payload)
            else:
                # In production, we must enforce signature verification
                logger.error(f"Webhook signature verification failed in production mode: {str(sig_error)}")
                raise
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

        # Send appropriate notification email based on checkout mode
        try:
            # Get user email
            user_email = None
            if user_id:
                # Get user from auth.users
                user_response = subscription_service.supabase.table("users_view").select("email").eq("id", user_id).execute()
                if user_response.data and len(user_response.data) > 0:
                    user_email = user_response.data[0].get("email")

            # If we couldn't get the email from the user record, try to get it from the customer
            if not user_email and customer_id:
                # Get customer from Stripe
                customer = stripe_service.stripe.Customer.retrieve(customer_id)
                if customer and customer.get("email"):
                    user_email = customer.get("email")

            if user_email:
                # Check the mode to determine what type of email to send
                if mode == "subscription":
                    # Send subscription confirmation email
                    email_service.send_subscription_confirmation_email(user_email)
                    logger.info(f"Sent subscription confirmation email to {user_email}")
                elif mode == "payment":
                    # This is a one-time payment for additional credits
                    # Get the line items to determine how many credits were purchased
                    line_items = stripe_service.stripe.checkout.Session.list_line_items(session_id)

                    if line_items and line_items.data:
                        # Get the quantity from the first line item
                        quantity = line_items.data[0].quantity

                        # Get the product name to determine the credit amount
                        product_id = line_items.data[0].price.product
                        product = stripe_service.stripe.Product.retrieve(product_id)

                        # Extract credit count from product name or metadata
                        credit_count = 0
                        if "5 papers" in product.name.lower():
                            credit_count = 5
                        elif "10 papers" in product.name.lower():
                            credit_count = 10
                        elif "25 papers" in product.name.lower():
                            credit_count = 25
                        else:
                            # Try to get from metadata
                            credit_count = product.metadata.get("paper_credits", 0)

                        if credit_count > 0:
                            # Send credits confirmation email
                            email_service.send_credits_confirmation_email(user_email, int(credit_count) * quantity)
                            logger.info(f"Sent credits confirmation email to {user_email} for {credit_count * quantity} credits")
            else:
                logger.warning(f"Could not find email for user {user_id} or customer {customer_id}")
        except Exception as e:
            # Log the error but don't fail the webhook
            logger.error(f"Error sending notification email: {str(e)}")

    elif event_type == "customer.subscription.updated":
        subscription = event.get("data", {}).get("object", {})

        # Log subscription details
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        current_period_end = subscription.get("current_period_end")

        logger.info(f"Subscription updated: ID={subscription_id}, Customer={customer_id}, Status={status}, End={current_period_end}")

        # Find user by subscription ID
        try:
            response = subscription_service.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if response.data and len(response.data) > 0:
                user_id = response.data[0].get("user_id")

                # Get subscription end date
                if current_period_end:
                    from datetime import datetime
                    end_date = datetime.fromtimestamp(current_period_end)
                else:
                    from datetime import datetime, timedelta
                    end_date = datetime.now() + timedelta(days=30)

                # Update subscription status
                subscription_service.update_subscription(
                    user_id=user_id,
                    tier="premium",  # Keep the tier as premium
                    status=status,
                    end_date=end_date
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
                    papers_limit=0  # Reset to free tier limit
                )

                logger.info(f"Updated subscription for user {user_id} to free tier (canceled)")
            else:
                logger.error(f"No user found with subscription ID {subscription_id}")
        except Exception as e:
            logger.error(f"Error processing subscription.deleted: {str(e)}")

    # Return success for any event type
    return JSONResponse({"status": "success"})
