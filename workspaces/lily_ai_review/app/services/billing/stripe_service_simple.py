"""
Stripe service for handling payments and subscriptions.
"""
import stripe
from typing import Dict, Any, Optional

# Import configuration
from app.config import config

# Import logging
from app.logging import get_logger
logger = get_logger(__name__)

class StripeService:
    """Service for handling Stripe payments and subscriptions."""

    def __init__(self):
        """Initialize the Stripe service."""
        # Get Stripe API keys from config
        self.api_key = config.STRIPE_SECRET_KEY
        self.publishable_key = config.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = config.STRIPE_WEBHOOK_SECRET

        # Log the Stripe mode and publishable key for debugging
        logger.info(f"Initializing Stripe service in {config.get_stripe_mode()} mode")
        logger.info(f"Stripe publishable key: {self.publishable_key[:10]}...")

        # Set Stripe API key
        stripe.api_key = self.api_key

        # Get product and price IDs from config
        self.products = config.get_stripe_products()
        self.prices = config.get_stripe_prices()

        # Get payment links from config
        self.payment_links = config.get_stripe_payment_links()

    def get_publishable_key(self) -> str:
        """
        Get the Stripe publishable key.

        Returns:
            Stripe publishable key
        """
        # If publishable key is None or empty, log a warning
        if not self.publishable_key:
            logger.warning("Stripe publishable key is not configured")

            # Use a default test key in development mode
            if config.is_development() or config.is_testing():
                logger.warning("Using default test publishable key")
                return "pk_test_51QEfKbC1xrrQSUhiAPw3qp9JklymSvCcjgv9pv9D1NjYhiHMX9JNVYh01i7ZxXiVogkC0eOpH1XemEpzCWRIUJbh00PcDreZH0"

            # In production, this is a critical error
            if config.is_production():
                logger.error("No Stripe publishable key configured in production")

        return self.publishable_key

    def create_checkout_session(self, customer_email: str, user_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create a checkout session for a subscription.

        Args:
            customer_email: The customer's email address
            user_id: The user ID
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Checkout session
        """
        try:
            # Log the parameters for debugging
            logger.info(f"Creating checkout session for user {user_id} with email {customer_email}")
            logger.info(f"Success URL: {success_url}")
            logger.info(f"Cancel URL: {cancel_url}")
            logger.info(f"Premium price ID: {self.prices['premium']}")

            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": self.prices["premium"],
                        "quantity": 1
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    "user_id": user_id,
                    "tier": "premium"
                }
            )

            # Log the session URL for debugging
            logger.info(f"Created checkout session with URL: {session.url}")

            return session

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    def create_credits_checkout_session(self, credits_type: str, customer_email: str, user_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create a checkout session for paper credits.

        Args:
            credits_type: The type of credits to purchase ("credits_5", "credits_10", or "credits_25")
            customer_email: The customer's email address
            user_id: The user ID
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Checkout session
        """
        try:
            # Validate credits type
            if credits_type not in ["credits_5", "credits_10", "credits_25"]:
                raise ValueError(f"Invalid credits type: {credits_type}")

            # Get credit count
            credit_count = int(credits_type.split("_")[1])

            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": self.prices[credits_type],
                        "quantity": 1
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    "user_id": user_id,
                    "type": "paper_credits",
                    "credits": credit_count,
                    "product_id": self.products[credits_type]
                }
            )

            return session

        except Exception as e:
            logger.error(f"Error creating credits checkout session: {str(e)}")
            raise

    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """
        Create a customer portal session.

        Args:
            customer_id: The customer ID
            return_url: URL to redirect to after the customer portal session

        Returns:
            Customer portal session
        """
        try:
            # Create customer portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            return session

        except Exception as e:
            logger.error(f"Error creating customer portal session: {str(e)}")
            raise

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a subscription from Stripe.

        Args:
            subscription_id: The subscription ID

        Returns:
            Subscription data if found, None otherwise
        """
        try:
            # Get subscription
            subscription = stripe.Subscription.retrieve(subscription_id)

            return subscription

        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            return None

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a customer from Stripe.

        Args:
            customer_id: The customer ID

        Returns:
            Customer data if found, None otherwise
        """
        try:
            # Get customer
            customer = stripe.Customer.retrieve(customer_id)

            return customer

        except Exception as e:
            logger.error(f"Error getting customer: {str(e)}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a checkout session from Stripe.

        Args:
            session_id: The session ID

        Returns:
            Session data if found, None otherwise
        """
        try:
            # Get session
            session = stripe.checkout.Session.retrieve(session_id)

            return session

        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            return None

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle a Stripe webhook event.

        Args:
            payload: The webhook payload
            signature: The webhook signature

        Returns:
            Webhook event
        """
        try:
            # Log the webhook secret for debugging (first and last 5 chars only)
            if self.webhook_secret:
                logger.info(f"Using webhook secret: {self.webhook_secret[:5]}...{self.webhook_secret[-5:]}")
            else:
                logger.warning("No webhook secret configured")

            # Check if we're in development mode
            is_dev_mode = config.is_development()

            if is_dev_mode:
                # In development mode, parse the payload without verifying the signature
                logger.warning("Development mode: Bypassing webhook signature verification")
                import json
                event = json.loads(payload)
            else:
                # In production mode, verify the webhook signature
                try:
                    event = stripe.Webhook.construct_event(
                        payload, signature, self.webhook_secret
                    )
                    logger.info("Webhook signature verified successfully")
                except stripe.error.SignatureVerificationError as e:
                    # If signature verification fails, log the error and raise
                    logger.error(f"Webhook signature verification failed: {str(e)}")

                    # In production, we should not process unverified webhooks
                    if config.is_production():
                        raise

                    # In testing or development, we can still try to process the webhook
                    logger.warning("Non-production environment: Processing webhook without signature verification")
                    import json
                    event = json.loads(payload)
                    logger.info(f"Processing webhook event without verification: {event.get('type')}")

            return event

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise
