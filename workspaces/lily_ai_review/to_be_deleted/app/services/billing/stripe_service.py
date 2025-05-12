"""
Stripe service for handling payments and subscriptions.
This service provides methods for interacting with the Stripe API.
"""
import os
import stripe
import logging
import time
from typing import Dict, Any, List
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
        # Load environment variables
        load_dotenv()

        # Store Supabase client
        self.supabase_client = supabase_client

        # Get API key from environment variables
        self.api_key = os.getenv("STRIPE_API_KEY")

        # Check if API key is available
        if not self.api_key:
            logger.error("Stripe API key not found. Please set STRIPE_API_KEY in your .env file.")
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
        self.basic_price_id = None
        self.premium_price_id = None
        self.pro_price_id = None
        self.credits_5_price_id = None
        self.credits_10_price_id = None
        self.credits_15_price_id = None
        self.credits_25_price_id = None
        self.credits_20_price_id = None
        self.premium_product_id = None

        # Initialize payment links
        self.premium_payment_link = None

        # Load configuration from database or environment
        self._load_config()

        # Validate subscription price IDs
        if not all([self.basic_price_id, self.premium_price_id, self.pro_price_id]):
            logger.error("Stripe subscription price IDs not found. Please set all subscription price IDs in your .env file or database.")
            raise ValueError("Missing Stripe subscription price IDs")

        # Initialize payment links if not already set
        if not hasattr(self, 'premium_payment_link'):
            self.premium_payment_link = os.getenv("STRIPE_PAYMENT_LINK_PREMIUM")

        if not hasattr(self, 'credits_5_payment_link'):
            self.credits_5_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_5")

        if not hasattr(self, 'credits_10_payment_link'):
            self.credits_10_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_10")

        if not hasattr(self, 'credits_25_payment_link'):
            self.credits_25_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_25")

        # Validate payment links
        if not self.premium_payment_link:
            logger.warning("Premium payment link not found. Please set STRIPE_PAYMENT_LINK_PREMIUM in your .env file.")
            # Don't raise an error here to allow the application to start

        # Log payment links status
        logger.info(f"Payment links status:")
        logger.info(f"Premium: {'Available' if self.premium_payment_link else 'Not configured'}")
        logger.info(f"Credits 5: {'Available' if self.credits_5_payment_link else 'Not configured'}")
        logger.info(f"Credits 10: {'Available' if self.credits_10_payment_link else 'Not configured'}")
        logger.info(f"Credits 25: {'Available' if self.credits_25_payment_link else 'Not configured'}")

        # Validate credits price IDs
        if not all([self.credits_5_price_id, self.credits_10_price_id]):
            logger.warning("Stripe credits price IDs not found. Some functionality may be limited.")
            # Don't raise an error here, as this is not critical functionality

        logger.info(f"Initialized Stripe service in {self.environment} mode")

    def _load_config(self):
        """
        Load Stripe configuration from database or environment variables.
        """
        try:
            if self.supabase_client:
                logger.info("Attempting to load Stripe configuration from database")
                # Fetch all Stripe configuration from database
                response = self.supabase_client.table("saas_stripe_config").select("*").eq("is_active", True).execute()
                logger.info(f"Database response: {response}")

                if response.data:
                    config = {item["key"]: item["value"] for item in response.data}
                    logger.info(f"Loaded config from database: {config}")

                    # Set price IDs
                    self.basic_price_id = config.get("stripe_price_id_standard")
                    self.premium_price_id = config.get("stripe_price_id_premium")
                    self.pro_price_id = config.get("stripe_price_id_pro")

                    # Set credits price IDs
                    self.credits_5_price_id = config.get("stripe_price_id_credits_5")
                    self.credits_10_price_id = config.get("stripe_price_id_credits_10")
                    self.credits_15_price_id = config.get("stripe_price_id_credits_15")
                    self.credits_25_price_id = config.get("stripe_price_id_credits_25")

                    # Set product IDs
                    self.premium_product_id = config.get("stripe_product_id_premium")

                    # Set payment links
                    self.premium_payment_link = config.get("stripe_payment_link_premium")

                    logger.info(f"Loaded Stripe configuration from database: basic={self.basic_price_id}, premium={self.premium_price_id}, pro={self.pro_price_id}")
                    return
                else:
                    logger.warning("No Stripe configuration found in database")
        except Exception as e:
            logger.error(f"Error loading Stripe configuration from database: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        # Fall back to environment variables
        logger.info("Loading Stripe configuration from environment variables")
        if self.is_production:
            # Production IDs - these are commented out in .env during testing
            self.basic_price_id = os.getenv("STRIPE_PRICE_ID_STANDARD")
            self.premium_price_id = os.getenv("STRIPE_PRICE_ID_PREMIUM")
            self.pro_price_id = os.getenv("STRIPE_PRICE_ID_PRO", os.getenv("STRIPE_PRICE_ID_PREMIUM"))

            # Paper credits price IDs
            self.credits_5_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_5")
            self.credits_10_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_10")
            self.credits_20_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_20")

            # Payment links - production
            self.premium_payment_link = os.getenv("STRIPE_PAYMENT_LINK_PREMIUM")
            self.credits_5_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_5")
            self.credits_10_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_10")
            self.credits_25_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_25")
        else:
            # Test IDs - use the same variables for now
            self.basic_price_id = os.getenv("STRIPE_PRICE_ID_STANDARD")
            self.premium_price_id = os.getenv("STRIPE_PRICE_ID_PREMIUM")
            self.pro_price_id = os.getenv("STRIPE_PRICE_ID_PRO", os.getenv("STRIPE_PRICE_ID_PREMIUM"))

            # Paper credits price IDs
            self.credits_5_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_5")
            self.credits_10_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_10")
            self.credits_20_price_id = os.getenv("STRIPE_PRICE_ID_CREDITS_20")

            # Payment links - test
            self.premium_payment_link = os.getenv("STRIPE_PAYMENT_LINK_PREMIUM")
            self.credits_5_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_5")
            self.credits_10_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_10")
            self.credits_25_payment_link = os.getenv("STRIPE_PAYMENT_LINK_CREDITS_25")

        # Log payment links for debugging
        logger.info(f"Loaded payment links from environment variables:")
        logger.info(f"Premium: {self.premium_payment_link}")
        logger.info(f"Credits 5: {self.credits_5_payment_link}")
        logger.info(f"Credits 10: {self.credits_10_payment_link}")
        logger.info(f"Credits 25: {self.credits_25_payment_link}")

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

    def create_checkout_session(self, tier: str, customer_email: str, user_id: str) -> Dict[str, Any]:
        """
        Create a checkout session for subscription payments.

        Args:
            tier: The subscription tier (basic, premium, pro)
            customer_email: The customer's email address
            user_id: The internal user ID

        Returns:
            Dictionary containing the session ID and URL
        """
        # Determine price ID based on tier
        if tier == "basic" or tier == "standard":
            price_id = self.basic_price_id
            papers_limit = 3
            tier = "standard"  # Normalize tier name
        elif tier == "premium":
            price_id = self.premium_price_id
            papers_limit = 10
        elif tier == "pro":
            price_id = self.pro_price_id
            papers_limit = 999999  # Effectively unlimited
        else:
            raise ValueError(f"Invalid subscription tier: {tier}")

        try:
            # Get the base URL from environment variables
            base_url = os.getenv("BASE_URL", "https://researchassistant.uk")

            # Create success URL with session ID template variable
            # This will be replaced by Stripe with the actual session ID
            success_url = f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base_url}/billing/cancel"

            # First, check if the user already has a Stripe customer ID
            customer_id = None
            try:
                # Check if user already has a customer ID in our database
                # Use raw SQL query to avoid UUID conversion issues
                query = f"SELECT stripe_customer_id FROM saas_user_subscriptions WHERE user_id::text = '{user_id}';"
                response = self.supabase_client.table("saas_user_subscriptions").select("*").execute()
                logger.info(f"All subscriptions: {response.data}")

                # Execute the raw query
                response = self.supabase_client.postgrest.rpc(
                    "execute_sql",
                    {"query": query}
                ).execute()

                logger.info(f"Query response: {response.data}")

                if response.data and len(response.data) > 0 and response.data[0].get("stripe_customer_id"):
                    customer_id = response.data[0].get("stripe_customer_id")
                    logger.info(f"Found existing Stripe customer ID for user {user_id}: {customer_id}")
            except Exception as db_error:
                logger.error(f"Error checking for existing customer ID: {str(db_error)}")
                logger.error(f"Error details: {db_error}")
                # Continue without customer ID

            # If no customer ID found, create a new customer
            if not customer_id:
                try:
                    # Create a new customer in Stripe
                    customer = stripe.Customer.create(
                        email=customer_email,
                        metadata={
                            "user_id": user_id,
                            "tier": tier,
                            "papers_limit": papers_limit
                        }
                    )
                    customer_id = customer.id
                    logger.info(f"Created new Stripe customer for user {user_id}: {customer_id}")

                    # Store the customer ID in our database using raw SQL
                    try:
                        # First check if a record exists for this user
                        check_query = f"SELECT id FROM saas_user_subscriptions WHERE user_id::text = '{user_id}';"
                        check_response = self.supabase_client.postgrest.rpc(
                            "execute_sql",
                            {"query": check_query}
                        ).execute()

                        if check_response.data and len(check_response.data) > 0:
                            # Update existing record
                            update_query = f"UPDATE saas_user_subscriptions SET stripe_customer_id = '{customer_id}' WHERE user_id::text = '{user_id}';"
                            self.supabase_client.postgrest.rpc(
                                "execute_sql",
                                {"query": update_query}
                            ).execute()
                            logger.info(f"Updated user {user_id} with Stripe customer ID: {customer_id}")
                        else:
                            # No need to insert a new record here, as it should be created elsewhere
                            logger.info(f"No subscription record found for user {user_id}")
                    except Exception as update_error:
                        logger.error(f"Error updating user with customer ID: {str(update_error)}")
                        logger.error(f"Error details: {update_error}")
                        # Continue anyway
                except Exception as stripe_error:
                    logger.error(f"Error creating Stripe customer: {str(stripe_error)}")
                    logger.error(f"Error details: {stripe_error}")
                    # Continue without customer ID

            # Always create a direct checkout session with Stripe API
            try:
                # Create a checkout session with Stripe API
                checkout_params = {
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                    "payment_method_types": ["card"],
                    "line_items": [{
                        "price": price_id,
                        "quantity": 1
                    }],
                    "mode": "subscription",
                    "metadata": {
                        "user_id": user_id,
                        "tier": tier,
                        "papers_limit": papers_limit
                    }
                }

                # Use customer ID if available, otherwise use customer_email
                if customer_id:
                    checkout_params["customer"] = customer_id
                else:
                    checkout_params["customer_email"] = customer_email

                session = stripe.checkout.Session.create(**checkout_params)

                logger.info(f"Created Stripe checkout session: {session.id}")
                return {
                    "session_id": session.id,
                    "url": session.url
                }
            except Exception as stripe_error:
                logger.error(f"Error creating Stripe checkout session: {str(stripe_error)}")
                import traceback
                logger.error(traceback.format_exc())

                # Use a placeholder URL if checkout session creation fails
                stripe_url = f"{base_url}/billing/checkout-failed"
                logger.warning(f"Failed to create checkout session. Using placeholder: {stripe_url}")

                # Create a mock session ID for tracking
                mock_session_id = f"cs_mock_failed_{int(time.time())}"

                # Return error information
                return {
                    "session_id": mock_session_id,
                    "url": stripe_url,
                    "error": "Failed to create checkout session"
                }
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details from Stripe.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Dictionary containing subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
        except Exception as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            raise

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Dictionary containing the updated subscription
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return subscription
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise

    def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Reactivate a subscription that was set to cancel at period end.

        Args:
            subscription_id: The Stripe subscription ID

        Returns:
            Dictionary containing the updated subscription
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return subscription
        except Exception as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            raise

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: The raw request payload
            signature: The Stripe signature header

        Returns:
            Dictionary containing the event data

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

            # Return the event data
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get checkout session details.

        Args:
            session_id: The Stripe session ID

        Returns:
            Dictionary containing session details
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except Exception as e:
            logger.error(f"Error retrieving session: {str(e)}")
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

    def update_subscription(self, subscription_id: str, price_id: str) -> stripe.Subscription:
        """
        Update a subscription to a new plan.

        Args:
            subscription_id: Stripe subscription ID
            price_id: New Stripe price ID

        Returns:
            Updated Stripe Subscription object
        """
        try:
            # Get the subscription to retrieve the current items
            subscription = stripe.Subscription.retrieve(subscription_id)

            # Get the subscription item ID
            if not subscription.items.data:
                raise ValueError(f"No items found in subscription {subscription_id}")

            # Update the subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription.items.data[0].id,
                    'price': price_id,
                }],
            )

            logger.info(f"Updated subscription {subscription_id} to price {price_id}")
            return updated_subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error updating subscription {subscription_id}: {str(e)}")
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

    def construct_webhook_event(self, payload: bytes, signature: str) -> stripe.Event:
        """
        Construct a Stripe webhook event from payload and signature.

        Args:
            payload: The raw request payload
            signature: The Stripe-Signature header

        Returns:
            Stripe Event object
        """
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=signature,
                secret=self.webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error constructing webhook event: {str(e)}")
            raise

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current Stripe environment.

        Returns:
            Dictionary with environment information
        """
        return {
            "is_test": not self.is_production,
            "environment": "TEST" if not self.is_production else "PRODUCTION",
            "basic_price_id": self.basic_price_id,
            "premium_price_id": self.premium_price_id,
            "pro_price_id": self.pro_price_id
        }

    def create_credits_checkout_session(self, credits_amount: str, customer_email: str, user_id: str) -> Dict[str, Any]:
        """
        Create a checkout session for paper credits purchase.

        Args:
            credits_amount: The amount of credits to purchase ('5', '10', or '20')
            customer_email: The customer's email address
            user_id: The internal user ID

        Returns:
            Dictionary containing the session ID and URL
        """
        # Get the base URL from environment variables
        base_url = os.getenv("BASE_URL", "https://researchassistant.uk")

        # Create success URL with session ID template variable
        # This will be replaced by Stripe with the actual session ID
        success_url = f"{base_url}/billing/credits-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/billing/cancel"

        # First, check if the user already has a Stripe customer ID
        customer_id = None
        try:
            # Check if user already has a customer ID in our database
            # Use raw SQL query to avoid UUID conversion issues
            query = f"SELECT stripe_customer_id FROM saas_user_subscriptions WHERE user_id::text = '{user_id}';"

            # Execute the raw query
            response = self.supabase_client.postgrest.rpc(
                "execute_sql",
                {"query": query}
            ).execute()

            logger.info(f"Query response: {response.data}")

            if response.data and len(response.data) > 0 and response.data[0].get("stripe_customer_id"):
                customer_id = response.data[0].get("stripe_customer_id")
                logger.info(f"Found existing Stripe customer ID for user {user_id}: {customer_id}")
        except Exception as db_error:
            logger.error(f"Error checking for existing customer ID: {str(db_error)}")
            logger.error(f"Error details: {db_error}")
            # Continue without customer ID

        # If no customer ID found, create a new customer
        if not customer_id:
            try:
                # Create a new customer in Stripe
                customer = stripe.Customer.create(
                    email=customer_email,
                    metadata={
                        "user_id": user_id
                    }
                )
                customer_id = customer.id
                logger.info(f"Created new Stripe customer for user {user_id}: {customer_id}")

                # Store the customer ID in our database using raw SQL
                try:
                    # First check if a record exists for this user
                    check_query = f"SELECT id FROM saas_user_subscriptions WHERE user_id::text = '{user_id}';"
                    check_response = self.supabase_client.postgrest.rpc(
                        "execute_sql",
                        {"query": check_query}
                    ).execute()

                    if check_response.data and len(check_response.data) > 0:
                        # Update existing record
                        update_query = f"UPDATE saas_user_subscriptions SET stripe_customer_id = '{customer_id}' WHERE user_id::text = '{user_id}';"
                        self.supabase_client.postgrest.rpc(
                            "execute_sql",
                            {"query": update_query}
                        ).execute()
                        logger.info(f"Updated user {user_id} with Stripe customer ID: {customer_id}")
                    else:
                        # No need to insert a new record here, as it should be created elsewhere
                        logger.info(f"No subscription record found for user {user_id}")
                except Exception as update_error:
                    logger.error(f"Error updating user with customer ID: {str(update_error)}")
                    logger.error(f"Error details: {update_error}")
                    # Continue anyway
            except Exception as stripe_error:
                logger.error(f"Error creating Stripe customer: {str(stripe_error)}")
                logger.error(f"Error details: {stripe_error}")
                # Continue without customer ID

        # Determine credits amount and price ID
        if credits_amount == "5":
            credits = 5
            price_id = self.credits_5_price_id
        elif credits_amount == "10":
            credits = 10
            price_id = self.credits_10_price_id
        elif credits_amount == "20" or credits_amount == "25":
            credits = 25
            price_id = self.credits_25_price_id
        else:
            error_msg = f"Invalid credits amount: {credits_amount}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Check if price ID exists
        if not price_id:
            error_msg = f"No price ID found for {credits_amount} credits"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Always create a direct checkout session with Stripe API
        try:
            # Create a checkout session with Stripe API
            checkout_params = {
                "success_url": success_url,
                "cancel_url": cancel_url,
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1
                }],
                "mode": "payment",
                "metadata": {
                    "user_id": user_id,
                    "credits": credits,
                    "type": "paper_credits"
                }
            }

            # Use customer ID if available, otherwise use customer_email
            if customer_id:
                checkout_params["customer"] = customer_id
            else:
                checkout_params["customer_email"] = customer_email

            session = stripe.checkout.Session.create(**checkout_params)

            logger.info(f"Created Stripe checkout session for credits: {session.id}")
            return {
                "session_id": session.id,
                "url": session.url,
                "metadata": {
                    "user_id": user_id,
                    "credits": credits,
                    "type": "paper_credits"
                }
            }
        except Exception as stripe_error:
            logger.error(f"Error creating Stripe checkout session: {str(stripe_error)}")
            import traceback
            logger.error(traceback.format_exc())

            # Use a placeholder URL if checkout session creation fails
            stripe_url = f"{base_url}/billing/checkout-failed"
            logger.warning(f"Failed to create checkout session. Using placeholder: {stripe_url}")

            # Create a mock session ID for tracking
            mock_session_id = f"cs_mock_credits_failed_{int(time.time())}"

            # Return error information
            return {
                "session_id": mock_session_id,
                "url": stripe_url,
                "error": "Failed to create checkout session",
                "metadata": {
                    "user_id": user_id,
                    "credits": credits,
                    "type": "paper_credits"
                }
            }

    def get_publishable_key(self) -> str:
        """
        Get the Stripe publishable key.

        Returns:
            Stripe publishable key
        """
        return self.publishable_key
