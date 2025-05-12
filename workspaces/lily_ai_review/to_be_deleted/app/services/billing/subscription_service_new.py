"""
Subscription service for managing user subscriptions.

This service provides methods for managing user subscriptions in the database.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from app.models.subscription import Subscription, Payment
from app.services.billing.stripe_service_new import StripeService
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing user subscriptions."""

    _instance = None

    def __new__(cls):
        """Create a new instance of the SubscriptionService if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SubscriptionService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the subscription service."""
        self.supabase = get_supabase_client()
        self.stripe_service = StripeService(supabase_client=self.supabase)

        # Subscription tier details
        self.tier_limits = {
            "free": 1,        # Free tier - 1 paper
            "basic": 3,       # Basic tier - 3 papers
            "standard": 3,    # Standard tier - 3 papers (same as basic)
            "premium": 10,    # Premium tier - 10 papers
            "pro": 999999     # Pro tier - unlimited (effectively)
        }

    def get_user_subscription(self, user_id: str) -> Subscription:
        """
        Get a user's subscription data from the database.

        Args:
            user_id: The user ID

        Returns:
            Subscription object
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
                    "stripe_subscription_id": None,
                    "stripe_customer_id": None,
                    "start_date": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                # Insert default subscription
                insert_response = self.supabase.table("saas_user_subscriptions") \
                    .insert(subscription_data) \
                    .execute()

                if insert_response.data and len(insert_response.data) > 0:
                    subscription_data = insert_response.data[0]

                # Get additional credits
                additional_credits = self.get_user_additional_credits(user_id)
                subscription_data["additional_credits"] = additional_credits

                return Subscription.from_db_record(subscription_data)

            # Get the first subscription (users should only have one)
            subscription_data = response.data[0]

            # For premium tier, ensure papers_limit is 10
            if subscription_data.get("subscription_tier") == "premium" and subscription_data.get("papers_limit") != 10:
                logger.info(f"Fixing papers_limit for premium user {user_id} from {subscription_data.get('papers_limit')} to 10")
                subscription_data["papers_limit"] = 10

                # Update the subscription in the database
                self.supabase.table("saas_user_subscriptions") \
                    .update({"papers_limit": 10}) \
                    .eq("user_id", user_id) \
                    .execute()

            # Get additional credits
            additional_credits = self.get_user_additional_credits(user_id)
            subscription_data["additional_credits"] = additional_credits

            # Calculate subscription papers remaining and additional papers remaining
            papers_limit = subscription_data.get("papers_limit", 0)
            papers_used = subscription_data.get("papers_used", 0)
            papers_remaining = max(0, papers_limit - papers_used)

            subscription_data["subscription_papers_remaining"] = papers_remaining
            subscription_data["additional_papers_remaining"] = additional_credits

            # Calculate total papers remaining
            subscription_data["total_papers_remaining"] = papers_remaining + additional_credits

            return Subscription.from_db_record(subscription_data)

        except Exception as e:
            logger.error(f"Error getting user subscription: {str(e)}")
            # Return a default free subscription
            return Subscription(
                user_id=user_id,
                subscription_tier="free",
                status="active",
                papers_limit=self.tier_limits["free"],
                papers_used=0,
                papers_remaining=self.tier_limits["free"],
                additional_credits=0,
                subscription_papers_remaining=self.tier_limits["free"],
                additional_papers_remaining=0,
                total_papers_remaining=self.tier_limits["free"]
            )

    def get_user_additional_credits(self, user_id: str) -> int:
        """
        Get a user's additional paper credits.

        Args:
            user_id: The user ID

        Returns:
            Number of additional credits
        """
        try:
            # Get credits from saas_paper_credits
            response = self.supabase.table("saas_paper_credits") \
                .select("credits_remaining") \
                .eq("user_id", user_id) \
                .execute()

            # Check if credits exist
            if not response.data or len(response.data) == 0:
                return 0

            # Return the credits
            return response.data[0].get("credits_remaining", 0)
        except Exception as e:
            logger.error(f"Error getting user additional credits: {str(e)}")
            return 0

    def update_subscription(self, user_id: str, tier: str, status: str = "active",
                           papers_limit: Optional[int] = None, stripe_subscription_id: Optional[str] = None,
                           stripe_customer_id: Optional[str] = None) -> bool:
        """
        Update a user's subscription.

        Args:
            user_id: The user ID
            tier: The subscription tier
            status: The subscription status
            papers_limit: The papers limit (optional)
            stripe_subscription_id: The Stripe subscription ID (optional)
            stripe_customer_id: The Stripe customer ID (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current subscription
            current_subscription = self.get_user_subscription(user_id)

            # Set papers limit based on tier if not provided
            if papers_limit is None:
                papers_limit = self.tier_limits.get(tier, 0)

            # For premium tier, always ensure exactly 10 papers
            if tier == "premium":
                papers_limit = 10
                logger.info(f"Setting papers_limit to 10 for premium tier subscription for user {user_id}")

                # Reset papers_used to 0 for new premium subscriptions
                if status == "active" and current_subscription.subscription_tier != "premium":
                    papers_used = 0
                    logger.info(f"Resetting papers_used to 0 for new premium subscription for user {user_id}")
                else:
                    papers_used = current_subscription.papers_used
            else:
                papers_used = current_subscription.papers_used

            # Prepare update data
            update_data = {
                "subscription_tier": tier,
                "status": status,
                "papers_limit": papers_limit,
                "papers_used": papers_used,
                "updated_at": datetime.now().isoformat()
            }

            logger.info(f"Updating subscription for user {user_id}: tier={tier}, status={status}, papers_limit={papers_limit}, papers_used={papers_used}")

            # Add Stripe IDs if provided
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id
            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id

            # Update subscription
            self.supabase.table("saas_user_subscriptions") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()

            # Also update user metadata
            try:
                from auth.service import AuthService
                auth_service = AuthService()
                auth_service.update_user_metadata(user_id, {"subscription_tier": tier})
            except Exception as metadata_error:
                logger.error(f"Error updating user metadata: {str(metadata_error)}")

            return True
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
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

            # Verify subscription status with Stripe for premium users
            if subscription.stripe_subscription_id and subscription.subscription_tier != "free":
                is_active = self.verify_subscription_with_stripe(user_id)
                if not is_active:
                    return False

            # Use the model's method to check if the user can create a paper
            return subscription.can_create_paper()
        except Exception as e:
            logger.error(f"Error checking if user can create paper: {str(e)}")
            return False

    def verify_subscription_with_stripe(self, user_id: str, force_check: bool = False) -> bool:
        """
        Verify a user's subscription status directly with Stripe.

        Args:
            user_id: The user ID
            force_check: Force a check with Stripe even if last verification is recent

        Returns:
            True if the subscription is active, False otherwise
        """
        try:
            # Get the user's subscription from the database
            subscription = self.get_user_subscription(user_id)

            # Check if the subscription has a Stripe subscription ID
            if not subscription.stripe_subscription_id:
                return subscription.is_active()

            # Check if we need to verify with Stripe
            if subscription.last_verified and not force_check:
                current_time = datetime.now()
                time_since_verification = (current_time - subscription.last_verified).total_seconds()
                if time_since_verification < 86400:  # 24 hours
                    return subscription.is_active()

            # Get the subscription from Stripe
            stripe_subscription = self.stripe_service.get_subscription(subscription.stripe_subscription_id)

            # Check if the subscription is active
            is_active = stripe_subscription.get("status") in ["active", "trialing"]

            # Get the end date from Stripe
            current_period_end = stripe_subscription.get("current_period_end")
            if current_period_end:
                end_date = datetime.fromtimestamp(current_period_end)
            else:
                # If no end date from Stripe, use the existing one or set to 30 days from now
                end_date = subscription.end_date or (datetime.now() + timedelta(days=30))

            # Update the subscription in the database
            self.supabase.table("saas_user_subscriptions") \
                .update({
                    "status": "active" if is_active else "canceled",
                    "end_date": end_date.isoformat(),
                    "last_verified": datetime.now().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()

            return is_active
        except Exception as e:
            logger.error(f"Error verifying subscription with Stripe: {str(e)}")
            return subscription.is_active()  # Fall back to the database status

    def increment_papers_used(self, user_id: str) -> bool:
        """
        Increment the papers_used count for a user.
        Uses monthly papers first, then additional credits.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has monthly papers remaining
            if subscription.papers_remaining > 0:
                # Use a monthly paper
                new_count = subscription.papers_used + 1

                # Update subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update({"papers_used": new_count}) \
                    .eq("user_id", user_id) \
                    .execute()

                # Record usage in a new table for analytics
                try:
                    usage_data = {
                        "user_id": user_id,
                        "credit_type": "monthly",
                        "used_at": datetime.now().isoformat()
                    }
                    self.supabase.table("lily_paper_credit_usage") \
                        .insert(usage_data) \
                        .execute()
                except Exception as usage_error:
                    # Don't fail if usage recording fails
                    logger.error(f"Error recording paper credit usage: {str(usage_error)}")

                return True

            # Check if user has additional credits
            if subscription.additional_credits > 0:
                # Use an additional credit
                new_credits = subscription.additional_credits - 1

                # Update credits
                self.supabase.table("saas_paper_credits") \
                    .update({"credits_remaining": new_credits}) \
                    .eq("user_id", user_id) \
                    .execute()

                # Record usage in a new table for analytics
                try:
                    usage_data = {
                        "user_id": user_id,
                        "credit_type": "addon",
                        "used_at": datetime.now().isoformat()
                    }
                    self.supabase.table("lily_paper_credit_usage") \
                        .insert(usage_data) \
                        .execute()
                except Exception as usage_error:
                    # Don't fail if usage recording fails
                    logger.error(f"Error recording paper credit usage: {str(usage_error)}")

                return True

            # No credits available
            logger.error(f"User {user_id} has no credits available")
            return False

        except Exception as e:
            logger.error(f"Error incrementing papers used: {str(e)}")
            return False
