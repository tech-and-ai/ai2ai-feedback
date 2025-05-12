"""
Subscription service for managing user subscriptions.

This module provides a service for managing user subscriptions and paper credits.
"""
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from app.config import config
from app.logging import get_logger
from app.exceptions import PaymentError, ValidationError
from app.services.billing.stripe_service import StripeService

# Configure logger
logger = get_logger(__name__)

class SubscriptionService:
    """Service for managing user subscriptions."""

    def __init__(self):
        """Initialize the subscription service."""
        # Initialize Supabase client
        from app.services.supabase_service import get_supabase_client
        self.supabase = get_supabase_client()

        # Initialize Stripe service
        self.stripe_service = StripeService()

        # Log initialization
        logger.info("Initialized subscription service")

    def get_user_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's subscription.

        Args:
            user_id: The ID of the user

        Returns:
            Dict[str, Any]: The user's subscription
        """
        try:
            # Validate inputs
            if not user_id:
                raise ValidationError("No user ID provided")

            # Query the user's subscription
            response = self.supabase.table("saas_user_subscriptions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()

            # Check if subscription exists
            if not response.data or len(response.data) == 0:
                # Create a default subscription
                subscription = {
                    "user_id": user_id,
                    "subscription_tier": "free",
                    "status": "active",
                    "papers_limit": 0,
                    "papers_used": 0,
                    "papers_remaining": 0,
                    "additional_credits_remaining": 0,
                    "total_papers_remaining": 0
                }

                # Insert the default subscription
                self.supabase.table("saas_user_subscriptions") \
                    .insert(subscription) \
                    .execute()

                # Log the creation
                logger.info(f"Created default subscription for user: {user_id}")

                return subscription

            # Get the subscription
            subscription = response.data[0]

            # Calculate papers remaining
            papers_limit = subscription.get("papers_limit", 0)
            papers_used = subscription.get("papers_used", 0)
            papers_remaining = max(0, papers_limit - papers_used)

            # Get additional credits
            additional_credits_remaining = subscription.get("additional_credits_remaining", 0)

            # Calculate total papers remaining
            total_papers_remaining = papers_remaining + additional_credits_remaining

            # Add calculated fields
            subscription["papers_remaining"] = papers_remaining
            subscription["additional_credits_remaining"] = additional_credits_remaining
            subscription["total_papers_remaining"] = total_papers_remaining

            # Log the retrieval
            logger.info(f"Retrieved subscription for user: {user_id}")

            return subscription

        except Exception as e:
            # Log the error
            logger.error(f"Error getting user subscription: {str(e)}")

            # Return a default subscription
            return {
                "user_id": user_id,
                "subscription_tier": "free",
                "status": "active",
                "papers_limit": 0,
                "papers_used": 0,
                "papers_remaining": 0,
                "additional_credits_remaining": 0,
                "total_papers_remaining": 0
            }

    def update_subscription(self,
                           user_id: str,
                           tier: str = None,
                           status: str = None,
                           papers_limit: int = None,
                           papers_used: int = None,
                           additional_credits: int = None,
                           stripe_subscription_id: str = None,
                           stripe_customer_id: str = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """
        Update a user's subscription.

        Args:
            user_id: The ID of the user
            tier: The subscription tier (optional)
            status: The subscription status (optional)
            papers_limit: The papers limit (optional)
            papers_used: The papers used (optional)
            additional_credits: The additional credits (optional)
            stripe_subscription_id: The Stripe subscription ID (optional)
            stripe_customer_id: The Stripe customer ID (optional)
            end_date: The subscription end date (optional)

        Returns:
            Dict[str, Any]: The updated subscription
        """
        try:
            # Validate inputs
            if not user_id:
                raise ValidationError("No user ID provided")

            # Get the current subscription
            current_subscription = self.get_user_subscription(user_id)

            # Create update data
            update_data = {}

            # Add tier if provided
            if tier:
                update_data["subscription_tier"] = tier

            # Add status if provided
            if status:
                update_data["status"] = status

            # Add papers limit if provided
            if papers_limit is not None:
                update_data["papers_limit"] = papers_limit

            # Add papers used if provided
            if papers_used is not None:
                update_data["papers_used"] = papers_used

            # Add additional credits if provided
            if additional_credits is not None:
                # Get current additional credits
                current_additional_credits = current_subscription.get("additional_credits_remaining", 0)

                # Calculate new additional credits
                new_additional_credits = current_additional_credits + additional_credits

                # Update additional credits
                update_data["additional_credits_remaining"] = new_additional_credits

            # Add Stripe subscription ID if provided
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id

            # Add Stripe customer ID if provided
            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id

            # Add end date if provided
            if end_date:
                update_data["end_date"] = end_date.isoformat()

            # If no update data, return current subscription
            if not update_data:
                return current_subscription

            # Update the subscription
            response = self.supabase.table("saas_user_subscriptions") \
                .update(update_data) \
                .eq("user_id", user_id) \
                .execute()

            # Check if update was successful
            if not response.data or len(response.data) == 0:
                # Log the error
                logger.error(f"Failed to update subscription for user: {user_id}")

                # Return current subscription
                return current_subscription

            # Get the updated subscription
            updated_subscription = response.data[0]

            # Calculate papers remaining
            papers_limit = updated_subscription.get("papers_limit", 0)
            papers_used = updated_subscription.get("papers_used", 0)
            papers_remaining = max(0, papers_limit - papers_used)

            # Get additional credits
            additional_credits_remaining = updated_subscription.get("additional_credits_remaining", 0)

            # Calculate total papers remaining
            total_papers_remaining = papers_remaining + additional_credits_remaining

            # Add calculated fields
            updated_subscription["papers_remaining"] = papers_remaining
            updated_subscription["additional_credits_remaining"] = additional_credits_remaining
            updated_subscription["total_papers_remaining"] = total_papers_remaining

            # Log the update
            logger.info(f"Updated subscription for user: {user_id}")

            return updated_subscription

        except Exception as e:
            # Log the error
            logger.error(f"Error updating user subscription: {str(e)}")

            # Raise the error
            raise

    def handle_checkout_session_completed(self, session: Dict[str, Any]) -> bool:
        """
        Handle a completed checkout session.

        Args:
            session: The checkout session

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not session:
                logger.error("No checkout session provided")
                return False

            # Get session data
            session_id = session.get("id")
            customer_id = session.get("customer")
            metadata = session.get("metadata", {})
            user_id = metadata.get("user_id")
            mode = session.get("mode")

            # Log session details
            logger.info(f"Processing checkout session: {session_id}, Customer: {customer_id}, User: {user_id}, Mode: {mode}")

            # Check if user ID is provided
            if not user_id:
                logger.error(f"No user ID in session metadata: {session_id}")
                return False

            # Handle subscription mode
            if mode == "subscription":
                # Get subscription ID
                subscription_id = session.get("subscription")

                # Check if subscription ID is provided
                if not subscription_id:
                    logger.error(f"No subscription ID in session: {session_id}")
                    return False

                # Get subscription from Stripe
                subscription = self.stripe_service.get_subscription(subscription_id)

                # Check subscription status
                status = subscription.get("status")

                # Get subscription end date
                current_period_end = subscription.get("current_period_end")
                if current_period_end:
                    end_date = datetime.fromtimestamp(current_period_end)
                else:
                    end_date = datetime.now() + timedelta(days=30)

                # Update user subscription
                self.update_subscription(
                    user_id=user_id,
                    tier="premium",
                    status=status,
                    papers_limit=10,  # Premium tier gets 10 papers per month
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    end_date=end_date
                )

                # Log the update
                logger.info(f"Updated subscription for user {user_id} to premium tier")

                return True

            # Handle payment mode (for credits)
            elif mode == "payment":
                # Get line items
                line_items = session.get("line_items", {}).get("data", [])

                # Check if line items are provided
                if not line_items:
                    logger.error(f"No line items in session: {session_id}")
                    return False

                # Get the first line item
                line_item = line_items[0]

                # Get price ID
                price_id = line_item.get("price", {}).get("id")

                # Check if price ID is provided
                if not price_id:
                    logger.error(f"No price ID in line item: {session_id}")
                    return False

                # Determine credits amount based on price ID
                credits = 0
                if price_id == config.STRIPE_CREDITS_5_PRICE_ID:
                    credits = 5
                elif price_id == config.STRIPE_CREDITS_10_PRICE_ID:
                    credits = 10
                elif price_id == config.STRIPE_CREDITS_25_PRICE_ID:
                    credits = 25
                else:
                    logger.error(f"Unknown price ID: {price_id}")
                    return False

                # Update user subscription with additional credits
                self.update_subscription(
                    user_id=user_id,
                    additional_credits=credits,
                    stripe_customer_id=customer_id
                )

                # Log the update
                logger.info(f"Added {credits} credits for user {user_id}")

                return True

            # Unknown mode
            else:
                logger.error(f"Unknown checkout mode: {mode}")
                return False

        except Exception as e:
            # Log the error
            logger.error(f"Error handling checkout session: {str(e)}")

            # Return failure
            return False

    def verify_subscription_with_stripe(self, user_id: str) -> bool:
        """
        Verify a user's subscription status with Stripe.

        Args:
            user_id: The ID of the user

        Returns:
            bool: True if the user has an active premium subscription, False otherwise
        """
        try:
            # Validate inputs
            if not user_id:
                logger.warning("No user ID provided for subscription verification")
                return False

            # Get the current subscription from database
            subscription = self.get_user_subscription(user_id)

            # Check if user is on premium tier
            if subscription.get("subscription_tier") != "premium":
                logger.info(f"User {user_id} is not on premium tier")
                return False

            # Get Stripe subscription ID
            stripe_subscription_id = subscription.get("stripe_subscription_id")
            if not stripe_subscription_id:
                logger.warning(f"User {user_id} has no Stripe subscription ID")
                return False

            # Initialize Stripe service if not already initialized
            if not hasattr(self, "stripe_service"):
                from app.services.billing.stripe_service import StripeService
                self.stripe_service = StripeService()

            # Get subscription from Stripe
            stripe_subscription = self.stripe_service.get_subscription(stripe_subscription_id)

            # Check subscription status
            status = stripe_subscription.get("status")

            # Valid statuses: active, trialing
            valid_statuses = ["active", "trialing"]
            is_valid = status in valid_statuses

            if is_valid:
                logger.info(f"Verified active subscription for user {user_id} with Stripe (status: {status})")
            else:
                logger.warning(f"User {user_id} subscription is not active in Stripe (status: {status})")

                # Update local subscription status and downgrade to free tier if not active
                if status not in valid_statuses:
                    self.update_subscription(
                        user_id=user_id,
                        tier="free" if status in ["canceled", "unpaid", "incomplete_expired"] else "premium",
                        status=status
                    )
                else:
                    self.update_subscription(
                        user_id=user_id,
                        status=status
                    )

            return is_valid

        except Exception as e:
            # Log the error
            logger.error(f"Error verifying subscription with Stripe: {str(e)}")

            # Return failure
            return False

    def use_paper_credit(self, user_id: str) -> bool:
        """
        Use a paper credit for a user.

        Args:
            user_id: The ID of the user

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not user_id:
                raise ValidationError("No user ID provided")

            # Get the current subscription
            subscription = self.get_user_subscription(user_id)

            # Check if user has any credits
            total_papers_remaining = subscription.get("total_papers_remaining", 0)

            if total_papers_remaining <= 0:
                logger.warning(f"User {user_id} has no paper credits remaining")
                return False

            # Determine which type of credit to use
            papers_remaining = subscription.get("papers_remaining", 0)
            additional_credits_remaining = subscription.get("additional_credits_remaining", 0)

            # Use subscription papers first, then additional credits
            if papers_remaining > 0:
                # Increment papers used
                papers_used = subscription.get("papers_used", 0) + 1

                # Update subscription
                self.update_subscription(
                    user_id=user_id,
                    papers_used=papers_used
                )

                # Log the update
                logger.info(f"Used subscription paper credit for user {user_id}, {papers_remaining - 1} remaining")

            else:
                # Use additional credit
                new_additional_credits = additional_credits_remaining - 1

                # Update subscription
                self.update_subscription(
                    user_id=user_id,
                    additional_credits=new_additional_credits - additional_credits_remaining
                )

                # Log the update
                logger.info(f"Used additional paper credit for user {user_id}, {new_additional_credits} remaining")

            return True

        except Exception as e:
            # Log the error
            logger.error(f"Error using paper credit: {str(e)}")

            # Return failure
            return False
