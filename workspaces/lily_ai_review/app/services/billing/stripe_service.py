"""
Stripe service for handling payments and subscriptions.

This module provides a service for interacting with the Stripe API.
"""
import stripe
from typing import Dict, Any

from app.exceptions import PaymentError
from app.services.base_service import ApiService

class StripeService(ApiService):
    """Service for interacting with the Stripe API."""

    def __init__(self):
        """Initialize the Stripe service."""
        super().__init__()

        # Set the API key
        self.api_key = self.config.STRIPE_API_KEY or self.config.STRIPE_SECRET_KEY
        if not self.api_key:
            self.logger.warning("No Stripe API key provided")

        # Configure Stripe
        stripe.api_key = self.api_key

        # Set webhook secret
        self.webhook_secret = self.config.STRIPE_WEBHOOK_SECRET

        # Log initialization
        self.logger.info(f"Initialized Stripe service in {self.config.get_stripe_mode()} mode")

    def get_client(self):
        """
        Get the Stripe client.

        Returns:
            The Stripe client
        """
        return stripe

    def create_checkout_session(self,
                               price_id: str,
                               success_url: str,
                               cancel_url: str,
                               customer_email: str = None,
                               customer_id: str = None,
                               metadata: Dict[str, str] = None,
                               mode: str = "subscription") -> Dict[str, Any]:
        """
        Create a Stripe checkout session.

        Args:
            price_id: The ID of the price to create the checkout session for
            success_url: The URL to redirect to after successful payment
            cancel_url: The URL to redirect to if payment is canceled
            customer_email: The customer's email address (optional)
            customer_id: The customer's Stripe ID (optional)
            metadata: Additional metadata to include in the checkout session
            mode: The mode of the checkout session (subscription or payment)

        Returns:
            Dict[str, Any]: The checkout session

        Raises:
            PaymentError: If there is an error creating the checkout session
        """
        try:
            # Validate inputs
            if not price_id:
                raise PaymentError("No price ID provided")

            if not success_url:
                raise PaymentError("No success URL provided")

            if not cancel_url:
                raise PaymentError("No cancel URL provided")

            # Create line items
            line_items = [
                {
                    "price": price_id,
                    "quantity": 1
                }
            ]

            # Create session parameters
            session_params = {
                "line_items": line_items,
                "mode": mode,
                "success_url": success_url,
                "cancel_url": cancel_url,
            }

            # Add customer email if provided
            if customer_email:
                session_params["customer_email"] = customer_email

            # Add customer ID if provided
            if customer_id:
                session_params["customer"] = customer_id

            # Add metadata if provided
            if metadata:
                session_params["metadata"] = metadata

            # Create the checkout session
            session = stripe.checkout.Session.create(**session_params)

            # Log the session creation
            self.logger.info(f"Created Stripe checkout session: {session.id}")

            return session

        except stripe.error.StripeError as e:
            # Log the error
            self.logger.error(f"Stripe error creating checkout session: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Error creating checkout session: {str(e)}")

        except Exception as e:
            # Log the error
            self.logger.error(f"Unexpected error creating checkout session: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Unexpected error creating checkout session: {str(e)}")

    def retrieve_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a Stripe checkout session.

        Args:
            session_id: The ID of the checkout session to retrieve

        Returns:
            Dict[str, Any]: The checkout session

        Raises:
            PaymentError: If there is an error retrieving the checkout session
        """
        try:
            # Validate inputs
            if not session_id:
                raise PaymentError("No session ID provided")

            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)

            # Log the session retrieval
            self.logger.info(f"Retrieved Stripe checkout session: {session.id}")

            return session

        except stripe.error.StripeError as e:
            # Log the error
            self.logger.error(f"Stripe error retrieving checkout session: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Error retrieving checkout session: {str(e)}")

        except Exception as e:
            # Log the error
            self.logger.error(f"Unexpected error retrieving checkout session: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Unexpected error retrieving checkout session: {str(e)}")

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle a Stripe webhook event.

        Args:
            payload: The webhook payload
            signature: The webhook signature

        Returns:
            Dict[str, Any]: The webhook event

        Raises:
            PaymentError: If there is an error handling the webhook
        """
        try:
            # Validate inputs
            if not payload:
                raise PaymentError("No webhook payload provided")

            if not signature:
                raise PaymentError("No webhook signature provided")

            if not self.webhook_secret:
                raise PaymentError("No webhook secret configured")

            # Verify the webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            # Log the event
            self.logger.info(f"Verified Stripe webhook event: {event.id} ({event.type})")

            return event

        except stripe.error.SignatureVerificationError as e:
            # Log the error
            self.logger.error(f"Stripe signature verification error: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Webhook signature verification failed: {str(e)}")

        except stripe.error.StripeError as e:
            # Log the error
            self.logger.error(f"Stripe error handling webhook: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Error handling webhook: {str(e)}")

        except Exception as e:
            # Log the error
            self.logger.error(f"Unexpected error handling webhook: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Unexpected error handling webhook: {str(e)}")

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get a subscription by ID.

        Args:
            subscription_id: The ID of the subscription to retrieve

        Returns:
            Dict[str, Any]: The subscription

        Raises:
            PaymentError: If there is an error retrieving the subscription
        """
        try:
            # Validate inputs
            if not subscription_id:
                raise PaymentError("No subscription ID provided")

            # Retrieve the subscription
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Log the subscription retrieval
            self.logger.info(f"Retrieved Stripe subscription: {subscription.id}")

            return subscription

        except stripe.error.StripeError as e:
            # Log the error
            self.logger.error(f"Stripe error retrieving subscription: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Error retrieving subscription: {str(e)}")

        except Exception as e:
            # Log the error
            self.logger.error(f"Unexpected error retrieving subscription: {str(e)}")

            # Raise a payment error
            raise PaymentError(f"Unexpected error retrieving subscription: {str(e)}")
