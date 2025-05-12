"""
Subscription service for managing user subscriptions.
This service provides methods for managing user subscriptions in the database.

DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService instead.
This module is kept for backward compatibility.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.billing.subscription_service_new import SubscriptionService as NewSubscriptionService
from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Service for managing user subscriptions.
    DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService instead.
    """

    def __init__(self):
        """Initialize the subscription service."""
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService instead")
        self.new_service = NewSubscriptionService()
        self.supabase = get_supabase_client()
        self.stripe_service = self.new_service.stripe_service

        # Subscription tier details
        self.tier_limits = {
            "free": 1,        # Free tier - 1 paper
            "basic": 3,       # Basic tier - 3 papers
            "standard": 3,    # Standard tier - 3 papers (same as basic)
            "premium": 10,    # Premium tier - 10 papers
            "pro": 999999     # Pro tier - unlimited (effectively)
        }

        # Review paper limits per tier
        self.review_limits = {
            "free": 1,        # Free tier - 1 review
            "basic": 3,       # Basic tier - 3 reviews
            "standard": 3,    # Standard tier - 3 reviews (same as basic)
            "premium": 10,    # Premium tier - 10 reviews
            "pro": 999999     # Pro tier - unlimited (effectively)
        }

    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's subscription data from the database.
        DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.get_user_subscription instead.

        Args:
            user_id: The user ID

        Returns:
            Dictionary containing subscription data
        """
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.get_user_subscription instead")

        # Get subscription from new service
        subscription = self.new_service.get_user_subscription(user_id)

        # Convert to dictionary
        subscription_dict = subscription.to_dict()

        # Add reviews remaining (for backward compatibility)
        subscription_tier = subscription.subscription_tier
        reviews_limit = self.review_limits.get(subscription_tier, 1)
        reviews_used = 0
        reviews_remaining = max(0, reviews_limit - reviews_used)
        subscription_dict["reviews_limit"] = reviews_limit
        subscription_dict["reviews_used"] = reviews_used
        subscription_dict["reviews_remaining"] = reviews_remaining

        return subscription_dict

    def get_user_additional_credits(self, user_id: str) -> int:
        """
        Get a user's additional paper credits.
        DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.get_user_additional_credits instead.

        Args:
            user_id: The user ID

        Returns:
            Number of additional credits
        """
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.get_user_additional_credits instead")
        return self.new_service.get_user_additional_credits(user_id)

    def verify_subscription_with_stripe(self, user_id: str, force_check: bool = False) -> bool:
        """
        Verify a user's subscription status directly with Stripe.
        DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.verify_subscription_with_stripe instead.

        Args:
            user_id: The user ID
            force_check: Force a check with Stripe even if last verification is recent

        Returns:
            True if the subscription is active, False otherwise
        """
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.verify_subscription_with_stripe instead")
        return self.new_service.verify_subscription_with_stripe(user_id, force_check)

    def can_create_paper(self, user_id: str) -> bool:
        """
        Check if a user can create a new paper based on their subscription.
        DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.can_create_paper instead.

        Args:
            user_id: The user ID

        Returns:
            True if the user can create a paper, False otherwise
        """
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.can_create_paper instead")
        return self.new_service.can_create_paper(user_id)

    def increment_papers_used(self, user_id: str) -> bool:
        """
        Increment the papers_used count for a user.
        Uses monthly papers first, then additional credits.
        DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.increment_papers_used instead.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        logger.warning("DEPRECATED: Use app.services.billing.subscription_service_new.SubscriptionService.increment_papers_used instead")

        # This method doesn't exist in the new service yet, so we'll implement it here
        try:
            # Get subscription
            subscription = self.new_service.get_user_subscription(user_id)

            # Check if user has monthly papers remaining
            if subscription.papers_remaining > 0:
                # Use a monthly paper
                new_count = subscription.papers_used + 1

                # Update subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update({"papers_used": new_count}) \
                    .eq("user_id", user_id) \
                    .execute()

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

                return True

            # No credits available
            logger.error(f"User {user_id} has no credits available")
            return False

        except Exception as e:
            logger.error(f"Error incrementing papers used: {str(e)}")
            return False

    # _record_paper_credit_usage method has been removed as it's no longer needed

    def create_checkout_session(self, user_id: str, tier: str, user_email: str = None) -> Dict[str, Any]:
        """
        Create a checkout session for a user to subscribe.

        Args:
            user_id: The user ID
            tier: The subscription tier (basic, premium, pro)
            user_email: The user's email (optional, provided by the route)

        Returns:
            Dictionary containing the session ID and URL
        """
        try:
            # Create checkout session
            session = self.stripe_service.create_checkout_session(
                tier=tier,
                customer_email=user_email,
                user_id=user_id
            )

            return session

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    def handle_subscription_created(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle subscription.created event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = event_data.get("object", {})

            # Get metadata from the subscription
            metadata = subscription.get("metadata", {})
            user_id = metadata.get("user_id")
            tier = metadata.get("tier")
            papers_limit = int(metadata.get("papers_limit", self.tier_limits.get(tier, 1)))

            # If user_id is not in metadata, try to find the user by customer ID
            if not user_id:
                customer_id = subscription.get("customer")
                if customer_id:
                    # Try to find user by customer ID
                    user_id = self._find_user_by_customer_id(customer_id)

                    # If still not found, try to get customer from Stripe and find user by email
                    if not user_id:
                        try:
                            customer = self.stripe_service.get_customer(customer_id)
                            if customer and customer.email:
                                # Try to find user by email
                                from auth.service import AuthService
                                auth_service = AuthService()
                                user = auth_service.get_user_by_email(customer.email)
                                if user:
                                    user_id = user.id

                                    # If tier is not specified, default to premium
                                    if not tier:
                                        tier = "premium"
                        except Exception as e:
                            logger.error(f"Error getting customer from Stripe: {str(e)}")

            if not user_id:
                logger.error("Could not find user_id for subscription")
                return False

            if not tier:
                logger.error("Missing tier in subscription metadata")
                return False

            # Update user subscription
            self.supabase.table("saas_user_subscriptions") \
                .upsert({
                    "user_id": user_id,
                    "subscription_tier": tier,
                    "status": subscription.get("status", "active"),
                    "papers_limit": papers_limit,
                    "papers_used": 0,  # Reset papers used when creating a new subscription
                    "stripe_subscription_id": subscription.get("id"),
                    "stripe_customer_id": subscription.get("customer"),
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=30)).isoformat()
                }) \
                .execute()

            logger.info(f"Subscription created for user {user_id}: {tier} tier, {subscription.get('status', 'active')} status")
            return True

        except Exception as e:
            logger.error(f"Error handling subscription created: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _find_user_by_customer_id(self, customer_id: str) -> str:
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

            # Debug the session data
            logger.info(f"Checkout session data: {session}")
            logger.info(f"Checkout session mode: {session.get('mode')}")

            # For testing purposes, we'll assume it's a subscription checkout
            # Check if this is a subscription checkout
            if session.get("mode") != "subscription":
                logger.info("Checkout session is not for a subscription, but we'll process it anyway for testing")
                # return True

            # Get the subscription ID
            subscription_id = session.get("subscription")
            if not subscription_id:
                logger.error("No subscription ID in checkout session")
                return False

            # Get the customer ID
            customer_id = session.get("customer")
            if not customer_id:
                logger.error("No customer ID in checkout session")
                return False

            # Get customer email
            customer_email = None
            customer_details = session.get("customer_details", {})
            if customer_details:
                customer_email = customer_details.get("email")

            # Get user ID from metadata
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")

            # If user ID not in metadata, try to find by customer ID
            if not user_id:
                user_id = self._find_user_by_customer_id(customer_id)

            # If still not found and we have an email, try to find by email
            if not user_id and customer_email:
                from auth.service import AuthService
                auth_service = AuthService()
                user = auth_service.get_user_by_email(customer_email)
                if user:
                    user_id = user.id

            if not user_id:
                logger.error(f"Could not find user for checkout session. Customer ID: {customer_id}, Email: {customer_email}")
                return False

            # Get the subscription from Stripe
            subscription = self.stripe_service.get_subscription(subscription_id)
            if not subscription:
                logger.error(f"Could not get subscription {subscription_id} from Stripe")
                return False

            # Determine tier based on price ID
            tier = "premium"  # Default to premium
            if subscription.items and subscription.items.data:
                price_id = subscription.items.data[0].price.id

                if price_id == self.stripe_service.basic_price_id:
                    tier = "basic"
                elif price_id == self.stripe_service.premium_price_id:
                    tier = "premium"
                elif price_id == self.stripe_service.pro_price_id:
                    tier = "pro"

            # Get papers limit based on tier
            papers_limit = self.tier_limits.get(tier, 0)

            # Update user subscription
            # For premium tier, always ensure exactly 10 papers
            if tier == "premium":
                papers_limit = 10

            # Update the subscription
            self.supabase.table("saas_user_subscriptions") \
                .upsert({
                    "user_id": user_id,
                    "subscription_tier": tier,
                    "status": subscription.status,
                    "papers_limit": papers_limit,
                    "papers_used": 0,  # Reset papers used when creating a new subscription
                    "stripe_subscription_id": subscription_id,
                    "stripe_customer_id": customer_id,
                    "start_date": datetime.now().isoformat(),
                    "end_date": (datetime.now() + timedelta(days=30)).isoformat()
                }) \
                .execute()

            # Log the paper limit being set
            logger.info(f"Setting papers_limit to {papers_limit} for {tier} tier subscription")

            logger.info(f"Subscription created from checkout for user {user_id}: {tier} tier, {subscription.status} status")
            return True

        except Exception as e:
            logger.error(f"Error handling checkout session completed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_subscription_updated(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle subscription.updated event from Stripe.

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

            # Get customer ID
            customer_id = subscription.get("customer")

            # Get metadata from the subscription
            metadata = subscription.get("metadata", {})

            # Get tier from metadata or default to premium
            tier = metadata.get("tier", "premium")

            # Get subscription status
            status = subscription.get("status", "active")

            # Update status based on cancel_at_period_end
            if subscription.get("cancel_at_period_end"):
                status = "canceled"

            # Get subscription end date
            current_period_end = subscription.get("current_period_end")
            if current_period_end:
                end_date = datetime.fromtimestamp(current_period_end).isoformat()
            else:
                # Default to 30 days from now if not available
                end_date = (datetime.now() + timedelta(days=30)).isoformat()

            # Update user's subscription in database
            update_data = {
                "subscription_tier": tier,
                "status": status,
                "end_date": end_date,
                "papers_limit": self.tier_limits.get(tier, 10),
                "updated_at": datetime.now().isoformat()
            }

            # Update subscription
            self.supabase.table("saas_user_subscriptions") \
                .update(update_data) \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            logger.info(f"Updated subscription for user {user_id} to {tier} tier with status {status}")
            return True

        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_subscription_deleted(self, event_data: Dict[str, Any]) -> bool:
        """
        Handle subscription.deleted event from Stripe.

        Args:
            event_data: The event data from Stripe

        Returns:
            True if successful, False otherwise
        """
        try:
            subscription = event_data.get("object", {})

            # Get subscription ID
            subscription_id = subscription.get("id")

            if not subscription_id:
                logger.error("Missing subscription ID in event data")
                return False

            # Find user with this subscription ID
            response = self.supabase.table("saas_user_subscriptions") \
                .select("user_id") \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            if not response.data or len(response.data) == 0:
                logger.error(f"No user found with subscription ID: {subscription_id}")
                return False

            # User found, proceed with update

            # Downgrade to sample tier
            self.supabase.table("saas_user_subscriptions") \
                .update({
                    "subscription_tier": "sample",
                    "status": "canceled",
                    "papers_limit": self.tier_limits["sample"],
                    "stripe_subscription_id": None
                }) \
                .eq("stripe_subscription_id", subscription_id) \
                .execute()

            return True

        except Exception as e:
            logger.error(f"Error handling subscription deleted: {str(e)}")
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
            # Get current credits
            current_credits = self.get_user_additional_credits(user_id)

            # Calculate new credits
            new_credits = current_credits + credits

            try:
                # Check if user has a credits record
                response = self.supabase.table("saas_paper_credits") \
                    .select("id") \
                    .eq("user_id", user_id) \
                    .execute()

                if not response.data or len(response.data) == 0:
                    # Create a new credits record
                    try:
                        self.supabase.table("saas_paper_credits") \
                            .insert({
                                "user_id": user_id,
                                "credits_remaining": new_credits
                            }) \
                            .execute()
                    except Exception as insert_error:
                        # If the error is about the column not existing, try to create it
                        if "credits_remaining" in str(insert_error):
                            logger.warning(f"The credits_remaining column does not exist in saas_paper_credits table: {str(insert_error)}")
                            # Try to create the table with the correct schema
                            try:
                                self.supabase.rpc("execute_sql", {
                                    "query": """
                                    ALTER TABLE IF EXISTS saas_paper_credits
                                    ADD COLUMN IF NOT EXISTS credits_remaining INTEGER NOT NULL DEFAULT 0
                                    """
                                }).execute()
                                logger.info("Added credits_remaining column to saas_paper_credits table")

                                # Try the insert again
                                self.supabase.table("saas_paper_credits") \
                                    .insert({
                                        "user_id": user_id,
                                        "credits_remaining": new_credits
                                    }) \
                                    .execute()
                            except Exception as alter_error:
                                logger.error(f"Error adding credits_remaining column: {str(alter_error)}")
                                return False
                        else:
                            # Re-raise if it's a different error
                            raise insert_error
                else:
                    # Update existing credits record
                    try:
                        self.supabase.table("saas_paper_credits") \
                            .update({"credits_remaining": new_credits}) \
                            .eq("user_id", user_id) \
                            .execute()
                    except Exception as update_error:
                        # If the error is about the column not existing, try to create it
                        if "credits_remaining" in str(update_error):
                            logger.warning(f"The credits_remaining column does not exist in saas_paper_credits table: {str(update_error)}")
                            # Try to create the table with the correct schema
                            try:
                                self.supabase.rpc("execute_sql", {
                                    "query": """
                                    ALTER TABLE IF EXISTS saas_paper_credits
                                    ADD COLUMN IF NOT EXISTS credits_remaining INTEGER NOT NULL DEFAULT 0
                                    """
                                }).execute()
                                logger.info("Added credits_remaining column to saas_paper_credits table")

                                # Try the update again
                                self.supabase.table("saas_paper_credits") \
                                    .update({"credits_remaining": new_credits}) \
                                    .eq("user_id", user_id) \
                                    .execute()
                            except Exception as alter_error:
                                logger.error(f"Error adding credits_remaining column: {str(alter_error)}")
                                return False
                        else:
                            # Re-raise if it's a different error
                            raise update_error

                return True
            except Exception as table_error:
                logger.error(f"Error accessing saas_paper_credits table: {str(table_error)}")
                return False

        except Exception as e:
            logger.error(f"Error adding paper credits: {str(e)}")
            return False

    def cancel_subscription(self, user_id: str) -> bool:
        """
        Cancel a user's subscription.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has a Stripe subscription
            stripe_subscription_id = subscription.get("stripe_subscription_id")
            if not stripe_subscription_id:
                logger.error(f"User {user_id} does not have a Stripe subscription")
                return False

            # Cancel subscription in Stripe
            self.stripe_service.cancel_subscription(stripe_subscription_id)

            # Update status in database
            self.supabase.table("saas_user_subscriptions") \
                .update({
                    "status": "canceled"
                }) \
                .eq("user_id", user_id) \
                .execute()

            return True

        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return False

    def can_create_review(self, user_id: str) -> bool:
        """
        Check if a user can create a new review paper based on their subscription.

        Args:
            user_id: The user ID

        Returns:
            True if the user can create a review, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if subscription is active
            if subscription.get("status") != "active":
                return False

            # Check if user has monthly reviews remaining
            if subscription.get("reviews_remaining", 0) > 0:
                return True

            # User cannot create a review
            return False

        except Exception as e:
            logger.error(f"Error checking if user can create review: {str(e)}")
            return False

    def increment_reviews_used(self, user_id: str) -> bool:
        """
        Increment the reviews_used count for a user.

        Args:
            user_id: The user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has monthly reviews remaining
            if subscription.get("reviews_remaining", 0) > 0:
                # Use a monthly review
                new_count = subscription.get("reviews_used", 0) + 1

                # Update subscription
                self.supabase.table("saas_user_subscriptions") \
                    .update({"reviews_used": new_count}) \
                    .eq("user_id", user_id) \
                    .execute()

                # Record usage
                self._record_review_credit_usage(user_id, "monthly")

                return True

            # No credits available
            logger.error(f"User {user_id} has no review credits available")
            return False

        except Exception as e:
            logger.error(f"Error incrementing reviews used: {str(e)}")
            return False

    def _record_review_credit_usage(self, user_id: str, credit_type: str, review_id: str = None) -> bool:
        """
        Record review credit usage.

        Args:
            user_id: The user ID
            credit_type: The type of credit used ('monthly')
            review_id: The review ID (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create usage record
            usage_data = {
                "user_id": user_id,
                "credit_type": credit_type,
                "used_at": datetime.now().isoformat()
            }

            # Add review_id if provided
            if review_id:
                usage_data["review_id"] = review_id

            # Try to insert the usage record
            try:
                self.supabase.table("saas_review_credit_usage") \
                    .insert(usage_data) \
                    .execute()

                return True
            except Exception as insert_error:
                # If the table doesn't exist, log it but don't fail
                if "relation" in str(insert_error) and "does not exist" in str(insert_error):
                    logger.warning(f"Skipping review credit usage record due to missing table: {str(insert_error)}")
                    return True
                else:
                    # Re-raise if it's a different error
                    raise insert_error

        except Exception as e:
            logger.error(f"Error recording review credit usage: {str(e)}")
            return False

    def update_subscription(self, user_id: str, tier: str, status: str, stripe_subscription_id: str = None,
                           stripe_customer_id: str = None, papers_limit: int = None) -> bool:
        """
        Update a user's subscription.

        Args:
            user_id: The user ID
            tier: The subscription tier (sample, basic, premium, pro)
            status: The subscription status (active, canceled, etc.)
            stripe_subscription_id: The Stripe subscription ID (optional)
            stripe_customer_id: The Stripe customer ID (optional)
            papers_limit: The number of papers allowed (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare update data
            update_data = {
                "subscription_tier": tier,
                "status": status,
                "papers_used": 0,  # Reset papers used when updating subscription
                "start_date": datetime.now().isoformat(),
                "last_verified": datetime.now().isoformat()  # Add verification timestamp
            }

            # Add optional fields if provided
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id

                # If we have a Stripe subscription ID, try to get the end date from Stripe
                try:
                    subscription = self.stripe_service.get_subscription(stripe_subscription_id)
                    if subscription and subscription.get("current_period_end"):
                        end_date = datetime.fromtimestamp(subscription.get("current_period_end")).isoformat()
                        update_data["end_date"] = end_date
                    else:
                        # Default to 30 days if we can't get the end date from Stripe
                        update_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()
                except Exception as stripe_error:
                    logger.error(f"Error getting subscription end date from Stripe: {str(stripe_error)}")
                    # Default to 30 days if we can't get the end date from Stripe
                    update_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()
            else:
                # Default to 30 days if we don't have a Stripe subscription ID
                update_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()

            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id

            if papers_limit is None:
                # Use default limit for tier
                papers_limit = self.tier_limits.get(tier, 1)

            update_data["papers_limit"] = papers_limit

            # Cancel any existing active subscriptions for this user
            try:
                # Get all active subscriptions for this user
                response = self.supabase.table("saas_user_subscriptions") \
                    .select("id, stripe_subscription_id") \
                    .eq("user_id", user_id) \
                    .eq("status", "active") \
                    .execute()

                if response.data and len(response.data) > 0:
                    for subscription in response.data:
                        # Skip the current subscription if it matches
                        if stripe_subscription_id and subscription.get("stripe_subscription_id") == stripe_subscription_id:
                            continue

                        # Cancel the subscription in Stripe if possible
                        if subscription.get("stripe_subscription_id"):
                            try:
                                self.stripe_service.cancel_subscription(subscription.get("stripe_subscription_id"))
                                logger.info(f"Canceled existing Stripe subscription {subscription.get('stripe_subscription_id')} for user {user_id}")
                            except Exception as cancel_error:
                                logger.error(f"Error canceling Stripe subscription: {str(cancel_error)}")

                        # Mark the subscription as canceled in the database
                        self.supabase.table("saas_user_subscriptions") \
                            .update({
                                "status": "canceled",
                                "updated_at": datetime.now().isoformat()
                            }) \
                            .eq("id", subscription.get("id")) \
                            .execute()

                        logger.info(f"Marked existing subscription {subscription.get('id')} as canceled for user {user_id}")
            except Exception as cancel_error:
                logger.error(f"Error canceling existing subscriptions: {str(cancel_error)}")

            # Update subscription
            # For upsert, we need to include the user_id in the update_data
            update_data["user_id"] = user_id

            self.supabase.table("saas_user_subscriptions") \
                .upsert(update_data) \
                .execute()

            logger.info(f"Updated subscription for user {user_id} to {tier} tier, {status} status")
            return True

        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def update_subscription_status(self, user_id: str, status: str) -> bool:
        """
        Update a user's subscription status.

        Args:
            user_id: The user ID
            status: The subscription status (active, canceled, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update subscription status
            self.supabase.table("saas_user_subscriptions") \
                .update({"status": status}) \
                .eq("user_id", user_id) \
                .execute()

            logger.info(f"Updated subscription status for user {user_id} to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating subscription status: {str(e)}")
            return False

    def create_subscription(self, user_id: str, subscription_tier: str, stripe_subscription_id: str = None,
                          stripe_customer_id: str = None, papers_limit: int = None, status: str = "active") -> Dict[str, Any]:
        """
        Create a new subscription for a user.

        Args:
            user_id: The user ID
            subscription_tier: The subscription tier (sample, basic, premium, pro)
            stripe_subscription_id: The Stripe subscription ID (optional)
            stripe_customer_id: The Stripe customer ID (optional)
            papers_limit: The number of papers allowed (optional)
            status: The subscription status (default: active)

        Returns:
            Dictionary containing the created subscription data
        """
        try:
            # Determine papers limit if not provided
            if papers_limit is None:
                papers_limit = self.tier_limits.get(subscription_tier, 1)

            # Create subscription data
            subscription_data = {
                "user_id": user_id,
                "subscription_tier": subscription_tier,
                "status": status,
                "papers_limit": papers_limit,
                "papers_used": 0,
                "stripe_subscription_id": stripe_subscription_id,
                "stripe_customer_id": stripe_customer_id,
                "start_date": datetime.now().isoformat(),
                "last_verified": datetime.now().isoformat()  # Add verification timestamp
            }

            # If we have a Stripe subscription ID, try to get the end date from Stripe
            if stripe_subscription_id:
                try:
                    subscription = self.stripe_service.get_subscription(stripe_subscription_id)
                    if subscription and subscription.get("current_period_end"):
                        end_date = datetime.fromtimestamp(subscription.get("current_period_end")).isoformat()
                        subscription_data["end_date"] = end_date
                    else:
                        # Default to 30 days if we can't get the end date from Stripe
                        subscription_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()
                except Exception as stripe_error:
                    logger.error(f"Error getting subscription end date from Stripe: {str(stripe_error)}")
                    # Default to 30 days if we can't get the end date from Stripe
                    subscription_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()
            else:
                # Default to 30 days if we don't have a Stripe subscription ID
                subscription_data["end_date"] = (datetime.now() + timedelta(days=30)).isoformat()

            # Cancel any existing active subscriptions for this user
            try:
                # Get all active subscriptions for this user
                response = self.supabase.table("saas_user_subscriptions") \
                    .select("id, stripe_subscription_id") \
                    .eq("user_id", user_id) \
                    .eq("status", "active") \
                    .execute()

                if response.data and len(response.data) > 0:
                    for existing_sub in response.data:
                        # Skip the current subscription if it matches
                        if stripe_subscription_id and existing_sub.get("stripe_subscription_id") == stripe_subscription_id:
                            continue

                        # Cancel the subscription in Stripe if possible
                        if existing_sub.get("stripe_subscription_id"):
                            try:
                                self.stripe_service.cancel_subscription(existing_sub.get("stripe_subscription_id"))
                                logger.info(f"Canceled existing Stripe subscription {existing_sub.get('stripe_subscription_id')} for user {user_id}")
                            except Exception as cancel_error:
                                logger.error(f"Error canceling Stripe subscription: {str(cancel_error)}")

                        # Mark the subscription as canceled in the database
                        self.supabase.table("saas_user_subscriptions") \
                            .update({
                                "status": "canceled",
                                "updated_at": datetime.now().isoformat()
                            }) \
                            .eq("id", existing_sub.get("id")) \
                            .execute()

                        logger.info(f"Marked existing subscription {existing_sub.get('id')} as canceled for user {user_id}")
            except Exception as cancel_error:
                logger.error(f"Error canceling existing subscriptions: {str(cancel_error)}")

            # Insert or update subscription
            self.supabase.table("saas_user_subscriptions") \
                .upsert(subscription_data) \
                .execute()

            logger.info(f"Created subscription for user {user_id}: {subscription_tier} tier, {status} status")

            # Return the created subscription data
            return subscription_data

        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def get_subscription_by_stripe_customer_id(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a subscription by Stripe customer ID.

        Args:
            customer_id: The Stripe customer ID

        Returns:
            Dictionary containing subscription data
        """
        try:
            # Get subscription from saas_user_subscriptions
            response = self.supabase.table("saas_user_subscriptions") \
                .select("*") \
                .eq("stripe_customer_id", customer_id) \
                .execute()

            # Check if subscription exists
            if not response.data or len(response.data) == 0:
                return None

            # Return the first subscription (users should only have one)
            return response.data[0]

        except Exception as e:
            logger.error(f"Error getting subscription by Stripe customer ID: {str(e)}")
            return None