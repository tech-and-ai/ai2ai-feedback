"""
Clean Subscription service for managing user subscriptions.
This service provides methods for managing user subscriptions in the database.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.services.billing.stripe_service_clean import StripeService
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing user subscriptions."""

    def __init__(self):
        """Initialize the subscription service."""
        self.supabase = get_supabase_client()
        self.stripe_service = StripeService(supabase_client=self.supabase)

        # Subscription tier details
        self.tier_limits = {
            "free": 1,        # Free tier - 1 paper
            "standard": 3,    # Standard tier - 3 papers
            "premium": 10,    # Premium tier - 10 papers
            "pro": 999999     # Pro tier - unlimited (effectively)
        }

    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's subscription data from the database.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing subscription data
        """
        try:
            # Get subscription from saas_user_subscriptions
            response = self.supabase.table("saas_user_subscriptions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()

            # Check if subscription exists
            if not response.data or len(response.data) == 0:
                # Create a sample subscription
                subscription_data = {
                    "user_id": user_id,
                    "subscription_tier": "sample",
                    "status": "active",
                    "papers_limit": self.tier_limits["sample"],
                    "papers_used": 0,
                    "subscription_papers_limit": self.tier_limits["sample"],
                    "subscription_papers_used": 0,
                    "additional_papers_limit": 0,
                    "additional_papers_used": 0,
                    "stripe_subscription_id": None,
                    "stripe_customer_id": None
                }

                # Insert sample subscription
                self.supabase.table("saas_user_subscriptions") \
                    .insert(subscription_data) \
                    .execute()

                return subscription_data

            # Get the first subscription (users should only have one)
            subscription_data = response.data[0]

            # Calculate subscription papers remaining
            subscription_papers_limit = subscription_data.get("subscription_papers_limit", 0)
            subscription_papers_used = subscription_data.get("subscription_papers_used", 0)
            subscription_papers_remaining = max(0, subscription_papers_limit - subscription_papers_used)
            subscription_data["subscription_papers_remaining"] = subscription_papers_remaining

            # Calculate additional papers remaining
            additional_papers_limit = subscription_data.get("additional_papers_limit", 0)
            additional_papers_used = subscription_data.get("additional_papers_used", 0)
            additional_papers_remaining = max(0, additional_papers_limit - additional_papers_used)
            subscription_data["additional_papers_remaining"] = additional_papers_remaining

            # Calculate total papers remaining (for backward compatibility)
            total_papers_remaining = subscription_papers_remaining + additional_papers_remaining
            subscription_data["papers_remaining"] = total_papers_remaining

            # For backward compatibility
            if "papers_limit" not in subscription_data or subscription_data["papers_limit"] is None:
                subscription_data["papers_limit"] = subscription_papers_limit + additional_papers_limit

            if "papers_used" not in subscription_data or subscription_data["papers_used"] is None:
                subscription_data["papers_used"] = subscription_papers_used + additional_papers_used

            # Add subscription status details
            status = subscription_data.get("status", "active")
            subscription_data["is_active"] = status == "active"
            subscription_data["is_canceled"] = status == "canceled"

            # Check if subscription is expired
            end_date = subscription_data.get("end_date")
            if end_date:
                try:
                    end_date_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    subscription_data["is_expired"] = end_date_dt < datetime.now()
                except (ValueError, TypeError):
                    subscription_data["is_expired"] = False
            else:
                subscription_data["is_expired"] = False

            return subscription_data

        except Exception as e:
            logger.error(f"Error getting user subscription: {str(e)}")
            # Return a default sample subscription
            return {
                "user_id": user_id,
                "subscription_tier": "sample",
                "status": "active",
                "is_active": True,
                "is_canceled": False,
                "is_expired": False,
                "papers_limit": self.tier_limits["sample"],
                "papers_used": 0,
                "papers_remaining": self.tier_limits["sample"],
                "subscription_papers_limit": self.tier_limits["sample"],
                "subscription_papers_used": 0,
                "subscription_papers_remaining": self.tier_limits["sample"],
                "additional_papers_limit": 0,
                "additional_papers_used": 0,
                "additional_papers_remaining": 0,
                "stripe_subscription_id": None,
                "stripe_customer_id": None
            }

    def create_checkout_session(self, user_id: str, user_email: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create a checkout session for a user to subscribe.

        Args:
            user_id: The user ID
            user_email: The user's email
            success_url: URL to redirect to after successful payment
            cancel_url: URL to redirect to if payment is cancelled

        Returns:
            Dictionary containing the session ID and URL
        """
        try:
            # Create checkout session
            session = self.stripe_service.create_checkout_session(
                customer_email=user_email,
                user_id=user_id,
                success_url=success_url,
                cancel_url=cancel_url
            )

            return session

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    def create_customer_portal_session(self, user_id: str, return_url: str) -> Dict[str, Any]:
        """
        Create a customer portal session for subscription management.

        Args:
            user_id: The user ID
            return_url: URL to redirect to after the customer portal session

        Returns:
            Dictionary containing the session URL
        """
        try:
            # Get user's subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has a Stripe customer ID
            customer_id = subscription.get("stripe_customer_id")
            if not customer_id:
                logger.error(f"User {user_id} does not have a Stripe customer ID")
                raise ValueError("User does not have a Stripe customer ID")

            # Create customer portal session
            portal_session = self.stripe_service.create_customer_portal_session(
                customer_id=customer_id,
                return_url=return_url
            )

            return portal_session

        except Exception as e:
            logger.error(f"Error creating customer portal session: {str(e)}")
            raise

    def handle_checkout_session_completed(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle checkout.session.completed event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            session = event_data.get("object", {})
            logger.info(f"Processing checkout.session.completed event: {session.get('id')}")

            # Get the customer ID from the session
            customer_id = session.get("customer")
            if not customer_id:
                logger.error("No customer ID in checkout session")
                return False

            # Get the user ID from session metadata
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")
            if not user_id:
                logger.error("No user ID in session metadata")
                return False

            # Check if this is a subscription checkout or a one-time payment
            if session.get("mode") == "subscription":
                # Handle subscription checkout
                # Get the subscription ID from the session
                subscription_id = session.get("subscription")
                if not subscription_id:
                    logger.error("No subscription ID in checkout session")
                    return False

                # Get subscription details from Stripe
                subscription = self.stripe_service.get_subscription(subscription_id)
                if not subscription:
                    logger.error(f"Could not retrieve subscription {subscription_id} from Stripe")
                    return False

                # Get subscription end date
                current_period_end = subscription.get("current_period_end")
                if current_period_end:
                    end_date = datetime.fromtimestamp(current_period_end).isoformat()
                else:
                    # Default to 30 days from now if not available
                    end_date = (datetime.now() + timedelta(days=30)).isoformat()

                # Get subscription details
                tier = metadata.get("tier", "premium")

                # For premium tier, always ensure exactly 10 papers
                if tier == "premium":
                    papers_limit = 10
                    logger.info(f"Setting papers_limit to 10 for premium tier subscription for user {user_id}")
                else:
                    papers_limit = self.tier_limits.get(tier, 10)
                    logger.info(f"Setting papers_limit to {papers_limit} for {tier} tier subscription for user {user_id}")

                # Reset papers_used to 0 for new subscriptions
                papers_used = 0
                logger.info(f"Resetting papers_used to 0 for new subscription for user {user_id}")

                # Update user's subscription in database
                self.update_subscription(
                    user_id=user_id,
                    tier=tier,
                    status="active",
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    end_date=end_date,
                    subscription_papers_limit=papers_limit,
                    papers_limit=papers_limit,  # Also set the legacy papers_limit field
                    papers_used=papers_used     # Reset papers used
                )

                # Send thank you email for new subscription
                try:
                    from app.services.email.email_service import EmailService
                    email_service = EmailService()

                    # Get user email from Supabase
                    user_email = None
                    try:
                        # First try to get email from auth.users table
                        user_response = self.supabase.rpc("execute_sql", {
                            "query": f"SELECT email FROM auth.users WHERE id = '{user_id}'"
                        }).execute()

                        if user_response.data and len(user_response.data) > 0:
                            user_email = user_response.data[0].get("email")
                            logger.info(f"Found user email in auth.users: {user_email}")

                        # If not found, try to get from session metadata
                        if not user_email and session and session.get("customer_email"):
                            user_email = session.get("customer_email")
                            logger.info(f"Using customer_email from session: {user_email}")

                        # Log if we still don't have an email
                        if not user_email:
                            logger.error(f"Could not find email for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error getting user email: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())

                    if user_email:
                        # Send thank you email
                        success = email_service.send_subscription_confirmation(
                            email=user_email,
                            tier=tier,
                            papers_limit=papers_limit,
                            end_date=end_date
                        )
                        if success:
                            logger.info(f"Successfully sent subscription confirmation email to {user_email}")
                        else:
                            logger.error(f"Failed to send subscription confirmation email to {user_email}")
                    else:
                        logger.error(f"Cannot send subscription confirmation email - no email found for user {user_id}")
                except Exception as email_error:
                    logger.error(f"Error sending subscription confirmation email: {str(email_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Continue even if email fails

                logger.info(f"Updated subscription for user {user_id} to {tier} tier")
                return True

            elif session.get("mode") == "payment":
                # Handle one-time payment (paper credits)
                # Get the line items from the session
                line_items = self.stripe_service.get_session_line_items(session.get("id"))
                if not line_items or len(line_items) == 0:
                    logger.error("No line items in checkout session")
                    return False

                # Process each line item
                for item in line_items:
                    # Get the price ID
                    price_id = item.get("price", {}).get("id")
                    if not price_id:
                        logger.error("No price ID in line item")
                        continue

                    # Get the product ID
                    product_id = item.get("price", {}).get("product")
                    if not product_id:
                        logger.error("No product ID in line item")
                        continue

                    # Get the product details
                    product = self.stripe_service.get_product(product_id)
                    if not product:
                        logger.error(f"Could not retrieve product {product_id} from Stripe")
                        continue

                    # Get the paper credits from the product metadata
                    product_metadata = product.get("metadata", {})
                    papers_str = product_metadata.get("papers")
                    if not papers_str:
                        logger.error(f"No papers metadata in product {product_id}")
                        continue

                    try:
                        papers_to_add = int(papers_str)
                    except (ValueError, TypeError):
                        logger.error(f"Invalid papers metadata value: {papers_str}")
                        continue

                    # Get the quantity
                    quantity = item.get("quantity", 1)
                    total_papers = papers_to_add * quantity

                    # Get the user's current subscription
                    subscription = self.get_user_subscription(user_id)
                    current_papers_limit = subscription.get("papers_limit", 0)

                    # Update the user's paper limit
                    new_papers_limit = current_papers_limit + total_papers

                    # Update the subscription in the database
                    self.update_subscription(
                        user_id=user_id,
                        tier=subscription.get("subscription_tier", "premium"),
                        status="active",
                        stripe_customer_id=customer_id,
                        additional_papers_limit=subscription.get("additional_papers_limit", 0) + total_papers
                    )

                    logger.info(f"Added {total_papers} paper credits to user {user_id}. New limit: {new_papers_limit}")

                return True

            else:
                logger.info(f"Checkout session {session.get('id')} has unsupported mode: {session.get('mode')}")
                return False

        except Exception as e:
            logger.error(f"Error handling checkout.session.completed event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_subscription_created(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle customer.subscription.created event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = event_data.get("object", {})
            logger.info(f"Processing customer.subscription.created event: {subscription.get('id')}")

            # Get subscription ID
            subscription_id = subscription.get("id")
            if not subscription_id:
                logger.error("No subscription ID in event data")
                return False

            # Get customer ID
            customer_id = subscription.get("customer")
            if not customer_id:
                logger.error("No customer ID in event data")
                return False

            # Get metadata
            metadata = subscription.get("metadata", {})

            # Get user ID from metadata
            user_id = metadata.get("user_id")

            # If user ID is not in metadata, try to find user by customer ID
            if not user_id:
                user_id = self._find_user_by_customer_id(customer_id)

            if not user_id:
                logger.error(f"Could not find user for subscription {subscription_id}")
                return False

            # Get tier from metadata or default to premium
            tier = metadata.get("tier", "premium")

            # Get subscription end date
            current_period_end = subscription.get("current_period_end")
            if current_period_end:
                end_date = datetime.fromtimestamp(current_period_end).isoformat()
            else:
                # Default to 30 days from now if not available
                end_date = (datetime.now() + timedelta(days=30)).isoformat()

            # Get papers limit based on tier
            papers_limit = self.tier_limits.get(tier, 10)

            # For premium tier, always ensure exactly 10 papers
            if tier == "premium":
                papers_limit = 10
                logger.info(f"Setting papers_limit to 10 for premium tier subscription for user {user_id}")

            # Reset papers_used to 0 for new subscriptions
            papers_used = 0
            logger.info(f"Resetting papers_used to 0 for new subscription for user {user_id}")

            # Update user's subscription in database
            self.update_subscription(
                user_id=user_id,
                tier=tier,
                status=subscription.get("status", "active"),
                stripe_subscription_id=subscription_id,
                stripe_customer_id=customer_id,
                end_date=end_date,
                subscription_papers_limit=papers_limit,
                papers_limit=papers_limit,
                papers_used=papers_used
            )

            # Send thank you email
            try:
                from app.services.email.email_service import EmailService
                email_service = EmailService()

                # Get user email from Supabase
                user_email = None
                try:
                    # First try to get email from auth.users table
                    user_response = self.supabase.rpc("execute_sql", {
                        "query": f"SELECT email FROM auth.users WHERE id = '{user_id}'"
                    }).execute()

                    if user_response.data and len(user_response.data) > 0:
                        user_email = user_response.data[0].get("email")
                        logger.info(f"Found user email in auth.users: {user_email}")

                    # If not found, try to get from customer data in Stripe
                    if not user_email and customer_id:
                        try:
                            customer = self.stripe_service.get_customer(customer_id)
                            if customer and customer.get("email"):
                                user_email = customer.get("email")
                                logger.info(f"Using email from Stripe customer: {user_email}")
                        except Exception as stripe_error:
                            logger.error(f"Error getting customer from Stripe: {str(stripe_error)}")

                    # Log if we still don't have an email
                    if not user_email:
                        logger.error(f"Could not find email for user {user_id}")
                except Exception as e:
                    logger.error(f"Error getting user email: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

                if user_email:
                    # Send thank you email
                    success = email_service.send_subscription_confirmation(
                        email=user_email,
                        tier=tier,
                        papers_limit=papers_limit,
                        end_date=end_date
                    )
                    if success:
                        logger.info(f"Successfully sent subscription confirmation email to {user_email}")
                    else:
                        logger.error(f"Failed to send subscription confirmation email to {user_email}")
                else:
                    logger.error(f"Cannot send subscription confirmation email - no email found for user {user_id}")
            except Exception as email_error:
                logger.error(f"Error sending subscription confirmation email: {str(email_error)}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue even if email fails

            logger.info(f"Created subscription for user {user_id}: {tier} tier")
            return True

        except Exception as e:
            logger.error(f"Error handling customer.subscription.created event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_subscription_updated(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle customer.subscription.updated event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = event_data.get("object", {})
            logger.info(f"Processing customer.subscription.updated event: {subscription.get('id')}")

            # Get subscription ID
            subscription_id = subscription.get("id")
            if not subscription_id:
                logger.error("No subscription ID in event data")
                return False

            # Find user by subscription ID
            response = self.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                logger.error(f"No user found with subscription ID {subscription_id}")
                return False

            user_id = response.data[0].get("user_id")

            # Get subscription status
            status = subscription.get("status", "active")

            # Update status based on cancel_at_period_end
            # Only mark as canceled if it's actually canceled, not just scheduled to cancel
            if subscription.get("cancel_at_period_end") and status != "active":
                status = "canceled"
            elif subscription.get("cancel_at_period_end"):
                # If it's scheduled to cancel but still active, log this but keep it active
                logger.info(f"Subscription {subscription_id} is scheduled to cancel at period end but is still active")

            # Get subscription end date
            current_period_end = subscription.get("current_period_end")
            if current_period_end:
                end_date = datetime.fromtimestamp(current_period_end).isoformat()
            else:
                # Keep existing end date if not available
                end_date = None

            # Update subscription in database
            self.update_subscription_status(
                user_id=user_id,
                status=status,
                end_date=end_date
            )

            logger.info(f"Updated subscription status for user {user_id} to {status}")
            return True

        except Exception as e:
            logger.error(f"Error handling customer.subscription.updated event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_subscription_deleted(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle customer.subscription.deleted event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = event_data.get("object", {})
            logger.info(f"Processing customer.subscription.deleted event: {subscription.get('id')}")

            # Get subscription ID
            subscription_id = subscription.get("id")
            if not subscription_id:
                logger.error("No subscription ID in event data")
                return False

            # Find user by subscription ID
            response = self.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                logger.error(f"No user found with subscription ID {subscription_id}")
                return False

            user_id = response.data[0].get("user_id")

            # Update subscription in database
            self.update_subscription_status(
                user_id=user_id,
                status="canceled"
            )

            logger.info(f"Deleted subscription for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling customer.subscription.deleted event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_webhook_event(self, event: Dict[str, Any]) -> bool:
        """
        Handle a Stripe webhook event.

        Args:
            event: The Stripe event

        Returns:
            True if the event was handled successfully, False otherwise
        """
        try:
            event_type = event.get("type")

            if not event_type:
                logger.error("Missing event type in webhook event")
                return False

            # Handle different event types
            if event_type == "checkout.session.completed":
                return self.handle_checkout_session_completed(event)
            elif event_type == "customer.subscription.created":
                return self.handle_subscription_created(event)
            elif event_type == "customer.subscription.updated":
                return self.handle_subscription_updated(event)
            elif event_type == "customer.subscription.deleted":
                return self.handle_subscription_deleted(event)
            else:
                logger.info(f"Ignoring unhandled event type: {event_type}")
                return True  # Return True to indicate the event was processed

        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def update_subscription(self, user_id: str, tier: str, status: str,
                           stripe_subscription_id: Optional[str] = None,
                           stripe_customer_id: Optional[str] = None,
                           end_date: Optional[str] = None,
                           papers_limit: Optional[int] = None,
                           subscription_papers_limit: Optional[int] = None,
                           additional_papers_limit: Optional[int] = None,
                           papers_used: Optional[int] = None) -> bool:
        """
        Update or create a user's subscription.

        Args:
            user_id: The user ID
            tier: The subscription tier
            status: The subscription status
            stripe_subscription_id: The Stripe subscription ID (optional)
            stripe_customer_id: The Stripe customer ID (optional)
            end_date: The subscription end date (optional)
            papers_limit: The total papers limit (optional, for backward compatibility)
            subscription_papers_limit: The subscription papers limit (optional)
            additional_papers_limit: The additional papers limit (optional)
            papers_used: The number of papers used (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update data
            update_data = {
                "subscription_tier": tier,
                "status": status
            }

            # Only include optional fields if they are provided
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id

            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id

            if end_date:
                update_data["end_date"] = end_date

            # Set papers_used if provided
            if papers_used is not None:
                update_data["papers_used"] = papers_used
                update_data["subscription_papers_used"] = papers_used

            # Handle papers limits
            if subscription_papers_limit is not None:
                update_data["subscription_papers_limit"] = subscription_papers_limit

                # For backward compatibility
                if papers_limit is None and additional_papers_limit is None:
                    # Get current additional papers limit
                    response = self.supabase.table("saas_user_subscriptions") \
                        .select("additional_papers_limit") \
                        .eq("user_id", user_id) \
                        .execute()

                    current_additional_limit = 0
                    if response.data and len(response.data) > 0:
                        current_additional_limit = response.data[0].get("additional_papers_limit", 0)

                    # Update total papers limit for backward compatibility
                    update_data["papers_limit"] = subscription_papers_limit + current_additional_limit

            if additional_papers_limit is not None:
                update_data["additional_papers_limit"] = additional_papers_limit

                # For backward compatibility
                if papers_limit is None and subscription_papers_limit is None:
                    # Get current subscription papers limit
                    response = self.supabase.table("saas_user_subscriptions") \
                        .select("subscription_papers_limit") \
                        .eq("user_id", user_id) \
                        .execute()

                    current_subscription_limit = 0
                    if response.data and len(response.data) > 0:
                        current_subscription_limit = response.data[0].get("subscription_papers_limit", 0)

                    # Update total papers limit for backward compatibility
                    update_data["papers_limit"] = current_subscription_limit + additional_papers_limit

            # If only the legacy papers_limit is provided, distribute it appropriately
            if papers_limit is not None and subscription_papers_limit is None and additional_papers_limit is None:
                # For a new subscription, set subscription_papers_limit to the tier limit
                # and additional_papers_limit to any remaining papers
                if status == "active" and tier != "sample":
                    tier_limit = self.tier_limits.get(tier, 0)
                    if papers_limit > tier_limit:
                        update_data["subscription_papers_limit"] = tier_limit
                        update_data["additional_papers_limit"] = papers_limit - tier_limit
                    else:
                        update_data["subscription_papers_limit"] = papers_limit
                        update_data["additional_papers_limit"] = 0
                else:
                    # For other cases, just set both to match the total
                    update_data["papers_limit"] = papers_limit

            # Reset papers_used counters if creating a new subscription
            if status == "active" and tier != "sample":
                update_data["papers_used"] = 0
                update_data["subscription_papers_used"] = 0
                # Don't reset additional_papers_used as these are purchased separately

            # Set start date for new subscriptions
            if stripe_subscription_id and status == "active":
                update_data["start_date"] = datetime.now().isoformat()

            # Check if subscription exists
            response = self.supabase.table("saas_user_subscriptions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                # Create new subscription
                self.supabase.table("saas_user_subscriptions") \
                    .insert({
                        "user_id": user_id,
                        **update_data
                    }) \
                    .execute()
            else:
                # Update existing subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update(update_data) \
                    .eq("user_id", user_id) \
                    .execute()

            # Update the user's tier in the auth.users table
            try:
                self.supabase.rpc("execute_sql", {
                    "query": f"""
                    UPDATE auth.users
                    SET raw_app_meta_data =
                        jsonb_set(
                            COALESCE(raw_app_meta_data, '{{}}'),
                            '{{subscription_tier}}',
                            '"{tier}"'
                        )
                    WHERE id = '{user_id}'
                    """
                }).execute()

                logger.info(f"Updated user {user_id} metadata with subscription tier {tier}")
            except Exception as e:
                logger.error(f"Error updating user metadata: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def update_subscription_status(self, user_id: str, status: str, end_date: Optional[str] = None) -> bool:
        """
        Update a user's subscription status.

        Args:
            user_id: The user ID
            status: The new subscription status
            end_date: The subscription end date (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update data
            update_data = {
                "status": status
            }

            if end_date:
                update_data["end_date"] = end_date

            # Update subscription
            self.supabase.table("saas_user_subscriptions") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()

            logger.info(f"Updated subscription status for user {user_id} to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating subscription status: {str(e)}")
            return False

    def can_create_paper(self, user_id: str) -> bool:
        """
        Check if a user can create a new paper based on their subscription.

        Args:
            user_id: The user ID

        Returns:
            True if the user can create a paper, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if subscription is active
            if not subscription.get("is_active", False):
                return False

            # Check if user has papers remaining (either subscription or additional)
            subscription_papers_remaining = subscription.get("subscription_papers_remaining", 0)
            additional_papers_remaining = subscription.get("additional_papers_remaining", 0)

            if subscription_papers_remaining > 0 or additional_papers_remaining > 0:
                return True

            # User cannot create a paper
            return False

        except Exception as e:
            logger.error(f"Error checking if user can create paper: {str(e)}")
            return False

    def increment_papers_used(self, user_id: str) -> bool:
        """
        Increment the papers_used count for a user.
        First uses subscription papers, then additional papers.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has papers remaining
            total_papers_remaining = subscription.get("papers_remaining", 0)
            if total_papers_remaining <= 0:
                logger.error(f"User {user_id} has no papers remaining")
                return False

            # Determine which counter to increment
            subscription_papers_remaining = subscription.get("subscription_papers_remaining", 0)

            update_data = {}

            # First use subscription papers, then additional papers
            if subscription_papers_remaining > 0:
                # Increment subscription_papers_used
                new_subscription_count = subscription.get("subscription_papers_used", 0) + 1
                update_data["subscription_papers_used"] = new_subscription_count
                logger.info(f"Incremented subscription_papers_used for user {user_id} to {new_subscription_count}")
            else:
                # Increment additional_papers_used
                new_additional_count = subscription.get("additional_papers_used", 0) + 1
                update_data["additional_papers_used"] = new_additional_count
                logger.info(f"Incremented additional_papers_used for user {user_id} to {new_additional_count}")

            # For backward compatibility, also increment the total papers_used
            new_total_count = subscription.get("papers_used", 0) + 1
            update_data["papers_used"] = new_total_count

            # Update subscription
            self.supabase.table("saas_user_subscriptions") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()

            logger.info(f"Incremented total papers_used for user {user_id} to {new_total_count}")
            return True

        except Exception as e:
            logger.error(f"Error incrementing papers used: {str(e)}")
            return False

    def _find_user_by_customer_id(self, customer_id: str) -> Optional[str]:
        """
        Find a user by Stripe customer ID.

        Args:
            customer_id: The Stripe customer ID

        Returns:
            User ID if found, None otherwise
        """
        try:
            # Find user by customer ID
            response = self.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_customer_id", customer_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                return None

            return response.data[0].get("user_id")

        except Exception as e:
            logger.error(f"Error finding user by customer ID: {str(e)}")
            return None