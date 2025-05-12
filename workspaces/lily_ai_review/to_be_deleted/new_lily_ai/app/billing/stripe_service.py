"""
Stripe service for handling payments and subscriptions.
"""
import os
import logging
import stripe
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

class StripeService:
    """Service for interacting with Stripe API."""

    def __init__(self):
        """Initialize the Stripe service."""
        # Get API keys from environment variables
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # Get payment links from environment variables
        self.payment_link_5_credits = os.getenv("STRIPE_PAYMENT_LINK_5_CREDITS")
        self.payment_link_10_credits = os.getenv("STRIPE_PAYMENT_LINK_10_CREDITS")
        self.payment_link_25_credits = os.getenv("STRIPE_PAYMENT_LINK_25_CREDITS")
        
        # Set API key for Stripe
        if self.api_key:
            stripe.api_key = self.api_key
        else:
            logger.warning("Stripe API key not set. Stripe functionality will be limited.")

    def get_publishable_key(self) -> str:
        """Get the Stripe publishable key."""
        return self.publishable_key or ""

    def create_customer(self, email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new customer in Stripe.

        Args:
            email: Customer's email
            name: Customer's name (optional)

        Returns:
            Stripe customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a customer from Stripe.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Stripe customer object
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer
        except Exception as e:
            logger.error(f"Error retrieving Stripe customer: {str(e)}")
            raise

    def create_subscription(
        self, 
        customer_id: str, 
        price_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            metadata: Additional metadata for the subscription

        Returns:
            Stripe subscription object
        """
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {"price": price_id},
                ],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe subscription: {subscription.id} for customer {customer_id}")
            return subscription
        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {str(e)}")
            raise

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe subscription object
        """
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Canceled Stripe subscription: {subscription_id}")
            return subscription
        except Exception as e:
            logger.error(f"Error canceling Stripe subscription: {str(e)}")
            raise

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get a subscription from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except Exception as e:
            logger.error(f"Error retrieving Stripe subscription: {str(e)}")
            raise

    def list_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        List all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of Stripe subscription objects
        """
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)
            return subscriptions.data
        except Exception as e:
            logger.error(f"Error listing Stripe subscriptions: {str(e)}")
            raise

    def create_checkout_session(
        self,
        price_id: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None,
        mode: str = "subscription"
    ) -> Dict[str, Any]:
        """
        Create a checkout session.

        Args:
            price_id: Stripe price ID
            customer_email: Customer's email
            success_url: URL to redirect to on success
            cancel_url: URL to redirect to on cancel
            metadata: Additional metadata for the session
            mode: Checkout mode ('subscription' or 'payment')

        Returns:
            Stripe checkout session object
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    },
                ],
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe checkout session: {session.id}")
            return session
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {str(e)}")
            raise

    def create_credits_checkout_session(
        self,
        credits_amount: str,
        customer_email: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a checkout session for paper credits.

        Args:
            credits_amount: Amount of credits to purchase ('5', '10', or '25')
            customer_email: Customer's email
            user_id: User ID

        Returns:
            Stripe checkout session object
        """
        # Get the appropriate payment link based on credits amount
        payment_link = None
        if credits_amount == "5":
            payment_link = self.payment_link_5_credits
        elif credits_amount == "10":
            payment_link = self.payment_link_10_credits
        elif credits_amount == "25":
            payment_link = self.payment_link_25_credits
        
        if not payment_link:
            logger.error(f"Payment link not found for credits amount: {credits_amount}")
            raise ValueError(f"Invalid credits amount: {credits_amount}")
        
        # If we're in test mode, create a mock session
        if not self.api_key or self.api_key.startswith("sk_test_"):
            # Create a mock session for testing
            import time
            mock_session_id = f"cs_mock_credits_{credits_amount}_{int(time.time())}"
            mock_url = f"/billing/credits-success?session_id={mock_session_id}"
            
            logger.info(f"Created mock checkout session: {mock_session_id}")
            return {
                "id": mock_session_id,
                "url": mock_url
            }
        
        # Create a real checkout session
        try:
            # Create a session with the payment link
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": payment_link,
                        "quantity": 1,
                    },
                ],
                mode="payment",
                success_url=f"{os.getenv('BASE_URL', 'http://localhost:8004')}/billing/credits-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.getenv('BASE_URL', 'http://localhost:8004')}/billing/manage",
                customer_email=customer_email,
                metadata={
                    "user_id": user_id,
                    "type": "paper_credits",
                    "credits": credits_amount
                }
            )
            logger.info(f"Created Stripe checkout session for credits: {session.id}")
            return session
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session for credits: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get a checkout session from Stripe.

        Args:
            session_id: Stripe session ID

        Returns:
            Stripe checkout session object
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except Exception as e:
            logger.error(f"Error retrieving Stripe session: {str(e)}")
            raise

    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Construct a Stripe event from webhook payload.

        Args:
            payload: Webhook payload
            sig_header: Stripe signature header

        Returns:
            Stripe event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except Exception as e:
            logger.error(f"Error constructing Stripe event: {str(e)}")
            raise
