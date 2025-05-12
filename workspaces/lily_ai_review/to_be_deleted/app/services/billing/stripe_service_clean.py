"""
Clean Stripe service for handling payments and subscriptions.
This service provides methods for interacting with the Stripe API.
"""
import os
import stripe
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class StripeService:
    """Service for interacting with Stripe API."""

    def __init__(self, supabase_client=None):
        """
        Initialize the Stripe service with the appropriate API key.

        Args:
            supabase_client: The Supabase client for database access
        """
        # Store Supabase client
        self.supabase_client = supabase_client

        # Get API key from environment variables
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            # Fallback to legacy variable name
            self.api_key = os.getenv("STRIPE_API_KEY")

        # Check if API key is available
        if not self.api_key:
            logger.error("Stripe API key not found. Please set STRIPE_SECRET_KEY in your .env file.")
            raise ValueError("Missing Stripe API key")

        # Environment detection
        self.is_production = "sk_live" in self.api_key
        self.environment = "production" if self.is_production else "test"

        # Configure Stripe with the API key
        stripe.api_key = self.api_key

        # Set webhook secret
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.webhook_secret:
            # Try legacy environment variables
            if self.is_production:
                self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET_LIVE")
            else:
                self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET_TEST")

            if not self.webhook_secret:
                logger.error("Stripe webhook secret not found. Please set STRIPE_WEBHOOK_SECRET in your .env file.")
                raise ValueError("Missing Stripe webhook secret")

        # Get publishable key
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        if not self.publishable_key:
            logger.error("Stripe publishable key not found. Please set STRIPE_PUBLISHABLE_KEY in your .env file.")
            raise ValueError("Missing Stripe publishable key")

        # Initialize product and price IDs
        self.premium_product_id = os.getenv("STRIPE_PREMIUM_PRODUCT_ID")
        self.premium_price_id = os.getenv("STRIPE_PREMIUM_PRICE_ID")

        if not self.premium_product_id:
            logger.error("Stripe premium product ID not found. Please set STRIPE_PREMIUM_PRODUCT_ID in your .env file.")

        if not self.premium_price_id:
            logger.error("Stripe premium price ID not found. Please set STRIPE_PREMIUM_PRICE_ID in your .env file.")

        logger.info(f"Initialized Stripe service in {self.environment} mode")

    def create_customer(self, email: str, name: str = None, metadata: Dict[str, Any] = None) -> stripe.Customer:
        """
        Create a new Stripe customer.

        Args:
            email: Customer's email address
            name: Customer's name (optional)
            metadata: Additional metadata for the customer (optional)

        Returns:
            Stripe Customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id} for email: {email}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    def create_checkout_session(self, customer_email: str, user_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create a checkout session for subscription payments.

        Args:
            customer_email: The customer's email address
            user_id: The internal user ID
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Dictionary containing the session ID and URL
        """
        try:
            if not self.premium_price_id:
                raise ValueError("Missing premium price ID")

            # Create the checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': self.premium_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={
                    'user_id': user_id,
                    'tier': 'premium'
                }
            )

            logger.info(f"Created checkout session: {session.id} for user: {user_id}")
            return {
                'session_id': session.id,
                'url': session.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """
        Create a customer portal session for subscription management.

        Args:
            customer_id: The Stripe customer ID
            return_url: URL to redirect to after the customer portal session

        Returns:
            Dictionary containing the session URL
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            logger.info(f"Created customer portal session for customer: {customer_id}")
            return {
                'url': session.url
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer portal session: {str(e)}")
            raise

    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Get subscription details from Stripe.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Stripe Subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            raise

    def get_customer(self, customer_id: str) -> stripe.Customer:
        """
        Get a customer by ID.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Stripe Customer object
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            raise

    def get_customer_subscriptions(self, customer_id: str) -> List[stripe.Subscription]:
        """
        Get all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of Stripe Subscription objects
        """
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)
            return subscriptions.data
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscriptions for customer {customer_id}: {str(e)}")
            raise

    def cancel_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Cancel a subscription immediately.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Updated Stripe Subscription object
        """
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Cancelled subscription: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise

    def cancel_subscription_at_period_end(self, subscription_id: str) -> stripe.Subscription:
        """
        Cancel a subscription at the end of the billing period.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Updated Stripe Subscription object
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            logger.info(f"Set subscription {subscription_id} to cancel at period end")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription at period end: {str(e)}")
            raise

    def reactivate_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Reactivate a subscription that was set to cancel at period end.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Updated Stripe Subscription object
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Reactivated subscription: {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            raise

    def handle_webhook(self, payload: bytes, signature: str) -> stripe.Event:
        """
        Handle Stripe webhook events.

        Args:
            payload: The raw request payload
            signature: The Stripe signature header

        Returns:
            Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If the signature verification fails
        """
        if not signature:
            logger.warning("Missing Stripe signature header")
            raise ValueError("Missing Stripe signature header")

        if not self.webhook_secret:
            logger.warning("Missing webhook secret. Cannot verify signature.")
            raise ValueError("Missing webhook secret")

        try:
            # Verify the webhook signature
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self.webhook_secret
            )

            logger.info(f"Successfully verified webhook signature for event: {event.get('type')}")
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise

    def get_session(self, session_id: str) -> stripe.checkout.Session:
        """
        Get checkout session details.

        Args:
            session_id: The Stripe session ID

        Returns:
            Stripe Session object
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving session: {str(e)}")
            raise

    def get_publishable_key(self) -> str:
        """
        Get the Stripe publishable key.

        Returns:
            Stripe publishable key
        """
        return self.publishable_key

    def get_session_line_items(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get line items for a checkout session.

        Args:
            session_id: The Stripe session ID

        Returns:
            List of line items
        """
        try:
            line_items = stripe.checkout.Session.list_line_items(session_id)
            return line_items.data
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving line items for session {session_id}: {str(e)}")
            return []

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get product details from Stripe.

        Args:
            product_id: The Stripe product ID

        Returns:
            Product details
        """
        try:
            product = stripe.Product.retrieve(product_id)
            return product
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving product {product_id}: {str(e)}")
            return None