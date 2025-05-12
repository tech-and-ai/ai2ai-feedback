"""
Subscription service for managing user subscriptions.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from auth.client_simple import get_supabase_client
# Import StripeService
# Use a relative import to avoid module not found errors
try:
    from .stripe_service_simple import StripeService
except ImportError:
    # Define a mock StripeService for testing
    class StripeService:
        """Mock StripeService for testing."""
        def __init__(self):
            """Initialize the mock Stripe service."""
            pass
from app.services.email.email_service_simple import EmailService

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing user subscriptions."""

    def __init__(self):
        """Initialize the subscription service."""
        self.supabase = get_supabase_client()
        self.stripe_service = StripeService()
        self.email_service = EmailService()

        # Subscription tier details
        self.tier_limits = {
            "free": 0,        # Free tier - 0 papers
            "premium": 10     # Premium tier - 10 papers
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
                # Create a default free subscription
                subscription_data = {
                    "user_id": user_id,
                    "subscription_tier": "free",
                    "status": "active",
                    "papers_limit": self.tier_limits["free"],
                    "papers_used": 0,
                    "additional_credits_remaining": 0,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Log the subscription data for debugging
                logger.info(f"Creating default subscription: {subscription_data}")

                # Insert default subscription
                insert_response = self.supabase.table("saas_user_subscriptions") \
                    .insert(subscription_data) \
                    .execute()

                if insert_response.data and len(insert_response.data) > 0:
                    subscription_data = insert_response.data[0]

                return subscription_data

            # Get the first subscription (users should only have one)
            subscription_data = response.data[0]

            # Calculate papers remaining
            papers_limit = subscription_data.get("papers_limit", 0)
            papers_used = subscription_data.get("papers_used", 0)
            papers_remaining = max(0, papers_limit - papers_used)
            subscription_data["papers_remaining"] = papers_remaining

            # Calculate additional credits
            additional_credits = subscription_data.get("additional_credits_remaining", 0)
            subscription_data["additional_credits_remaining"] = additional_credits

            # Calculate total papers remaining
            total_papers_remaining = papers_remaining + additional_credits
            subscription_data["total_papers_remaining"] = total_papers_remaining

            return subscription_data

        except Exception as e:
            logger.error(f"Error getting user subscription: {str(e)}")
            # Return a default free subscription
            return {
                "user_id": user_id,
                "subscription_tier": "free",
                "status": "active",
                "papers_limit": self.tier_limits["free"],
                "papers_used": 0,
                "papers_remaining": self.tier_limits["free"],
                "additional_credits_remaining": 0,
                "total_papers_remaining": self.tier_limits["free"]
            }

    def update_subscription(self, user_id: str, tier: str, status: str = "active",
                           stripe_subscription_id: Optional[str] = None,
                           stripe_customer_id: Optional[str] = None,
                           papers_limit: Optional[int] = None,
                           papers_used: Optional[int] = None,
                           additional_credits: Optional[int] = None) -> bool:
        """
        Update a user's subscription.

        Args:
            user_id: The user ID
            tier: The subscription tier
            status: The subscription status
            stripe_subscription_id: The Stripe subscription ID
            stripe_customer_id: The Stripe customer ID
            papers_limit: The papers limit
            papers_used: The papers used
            additional_credits: The additional credits

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update data
            update_data = {
                "subscription_tier": tier,
                "status": status,
                "updated_at": datetime.now().isoformat()
            }

            # Set papers limit based on tier if not provided
            if papers_limit is None:
                papers_limit = self.tier_limits.get(tier, 0)

            update_data["papers_limit"] = papers_limit

            # Set papers_used if provided
            if papers_used is not None:
                update_data["papers_used"] = papers_used

            # Set additional_credits if provided
            if additional_credits is not None:
                update_data["additional_credits_remaining"] = additional_credits

            # Set Stripe IDs if provided
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id

            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id

            # Check if subscription exists
            response = self.supabase.table("saas_user_subscriptions") \
                .select("id") \
                .eq("user_id", user_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                # Create new subscription
                self.supabase.table("saas_user_subscriptions") \
                    .insert({
                        "user_id": user_id,
                        "created_at": datetime.now().isoformat(),
                        **update_data
                    }) \
                    .execute()
            else:
                # Update existing subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update(update_data) \
                    .eq("user_id", user_id) \
                    .execute()

            # Update user metadata
            try:
                self.supabase.rpc("execute_sql", {
                    "query": f"""
                    UPDATE auth.users
                    SET raw_user_meta_data =
                        jsonb_set(
                            COALESCE(raw_user_meta_data, '{{}}'),
                            '{{subscription_tier}}',
                            '"{tier}"'
                        )
                    WHERE id = '{user_id}'
                    """
                }).execute()
            except Exception as e:
                logger.error(f"Error updating user metadata: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            return False

    def add_paper_credits(self, user_id: str, credits: int) -> bool:
        """
        Add paper credits to a user's account.

        Args:
            user_id: The user ID
            credits: The number of credits to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current subscription
            subscription = self.get_user_subscription(user_id)

            # Calculate new credits
            current_credits = subscription.get("additional_credits_remaining", 0)
            new_credits = current_credits + credits

            # Update subscription
            return self.update_subscription(
                user_id=user_id,
                tier=subscription.get("subscription_tier", "free"),
                additional_credits=new_credits
            )

        except Exception as e:
            logger.error(f"Error adding paper credits: {str(e)}")
            return False

    def increment_papers_used(self, user_id: str) -> bool:
        """
        Increment the papers_used count for a user.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has papers remaining
            if subscription.get("papers_remaining", 0) > 0:
                # Use a subscription paper
                new_count = subscription.get("papers_used", 0) + 1

                # Update subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update({"papers_used": new_count}) \
                    .eq("user_id", user_id) \
                    .execute()

                return True

            # Check if user has additional credits
            if subscription.get("additional_credits_remaining", 0) > 0:
                # Use an additional credit
                new_credits = subscription.get("additional_credits_remaining", 0) - 1

                # Update subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update({"additional_credits_remaining": new_credits}) \
                    .eq("user_id", user_id) \
                    .execute()

                return True

            # No papers remaining
            return False

        except Exception as e:
            logger.error(f"Error incrementing papers used: {str(e)}")
            return False

    def handle_checkout_session_completed(self, session: Dict[str, Any]) -> bool:
        """
        Handle checkout.session.completed event from Stripe.

        Args:
            session: The checkout session data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user ID from metadata
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")

            if not user_id:
                logger.error("No user_id in session metadata")
                return False

            # Get user email
            user_email = None
            try:
                user_response = self.supabase.rpc("execute_sql", {
                    "query": f"SELECT email FROM auth.users WHERE id = '{user_id}'"
                }).execute()

                if user_response.data and len(user_response.data) > 0:
                    user_email = user_response.data[0].get("email")
            except Exception as e:
                logger.error(f"Error getting user email: {str(e)}")

            # Check if this is a subscription or one-time payment
            if session.get("mode") == "subscription":
                # Handle subscription checkout
                subscription_id = session.get("subscription")
                customer_id = session.get("customer")

                if not subscription_id:
                    logger.error("No subscription ID in checkout session")
                    return False

                # Update subscription
                self.update_subscription(
                    user_id=user_id,
                    tier="premium",
                    status="active",
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    papers_limit=10,
                    papers_used=0
                )

                # Send confirmation email
                if user_email:
                    self.email_service.send_subscription_confirmation_email(user_email)

                return True

            elif session.get("mode") == "payment":
                # Handle one-time payment (paper credits)
                credits = int(metadata.get("credits", 0))

                if credits <= 0:
                    logger.error("Invalid credits value in metadata")
                    return False

                # Add credits to user's account
                self.add_paper_credits(user_id, credits)

                # Send confirmation email
                if user_email:
                    self.email_service.send_credits_confirmation_email(user_email, credits)

                return True

            else:
                logger.error(f"Unsupported checkout mode: {session.get('mode')}")
                return False

        except Exception as e:
            logger.error(f"Error handling checkout session: {str(e)}")
            return False
