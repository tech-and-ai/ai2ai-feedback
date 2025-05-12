"""
Subscription service for managing user subscriptions.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.database import get_db_client

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing user subscriptions."""

    def __init__(self):
        """Initialize the subscription service."""
        self.db_client = get_db_client()

    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's subscription.

        Args:
            user_id: User ID

        Returns:
            Subscription object or None if not found
        """
        try:
            # Query the database for the user's subscription
            query = """
            SELECT 
                s.id,
                s.user_id,
                s.subscription_tier,
                s.status,
                s.start_date,
                s.end_date,
                s.stripe_subscription_id,
                s.papers_used,
                s.papers_limit,
                s.additional_credits
            FROM 
                subscriptions s
            WHERE 
                s.user_id = $1
            ORDER BY 
                s.created_at DESC
            LIMIT 1
            """
            
            result = self.db_client.execute_query(query, [user_id])
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.info(f"No subscription found for user {user_id}")
                return None
            
            subscription = result["data"][0]
            
            # Calculate papers remaining
            papers_limit = subscription.get("papers_limit", 0)
            papers_used = subscription.get("papers_used", 0)
            additional_credits = subscription.get("additional_credits", 0)
            
            papers_remaining = max(0, papers_limit - papers_used) + additional_credits
            
            # Add calculated fields
            subscription["papers_remaining"] = papers_remaining
            
            return subscription
        except Exception as e:
            logger.error(f"Error getting user subscription: {str(e)}")
            return None

    def create_subscription(
        self, 
        user_id: str, 
        subscription_tier: str,
        status: str = "active",
        stripe_subscription_id: Optional[str] = None,
        papers_limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a subscription for a user.

        Args:
            user_id: User ID
            subscription_tier: Subscription tier ('free', 'premium', etc.)
            status: Subscription status ('active', 'canceled', etc.)
            stripe_subscription_id: Stripe subscription ID (optional)
            papers_limit: Number of papers included in the subscription
            start_date: Subscription start date (optional)
            end_date: Subscription end date (optional)

        Returns:
            Created subscription object or None if failed
        """
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = datetime.now()
            
            if not end_date:
                # Default to 30 days from start date
                end_date = start_date + timedelta(days=30)
            
            # Insert the subscription into the database
            query = """
            INSERT INTO subscriptions (
                user_id,
                subscription_tier,
                status,
                stripe_subscription_id,
                papers_limit,
                papers_used,
                additional_credits,
                start_date,
                end_date
            ) VALUES (
                $1, $2, $3, $4, $5, 0, 0, $6, $7
            )
            RETURNING id
            """
            
            result = self.db_client.execute_query(
                query, 
                [
                    user_id,
                    subscription_tier,
                    status,
                    stripe_subscription_id,
                    papers_limit,
                    start_date,
                    end_date
                ]
            )
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.error(f"Failed to create subscription for user {user_id}")
                return None
            
            subscription_id = result["data"][0]["id"]
            logger.info(f"Created subscription {subscription_id} for user {user_id}")
            
            # Get the created subscription
            return self.get_user_subscription(user_id)
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None

    def update_subscription(
        self, 
        subscription_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription ID
            updates: Dictionary of fields to update

        Returns:
            Updated subscription object or None if failed
        """
        try:
            # Build the update query dynamically based on the provided updates
            set_clauses = []
            params = []
            param_index = 1
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1
            
            # Add the subscription ID as the last parameter
            params.append(subscription_id)
            
            query = f"""
            UPDATE subscriptions
            SET {', '.join(set_clauses)}
            WHERE id = ${param_index}
            RETURNING user_id
            """
            
            result = self.db_client.execute_query(query, params)
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.error(f"Failed to update subscription {subscription_id}")
                return None
            
            user_id = result["data"][0]["user_id"]
            logger.info(f"Updated subscription {subscription_id} for user {user_id}")
            
            # Get the updated subscription
            return self.get_user_subscription(user_id)
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
            return None

    def cancel_subscription(self, user_id: str) -> bool:
        """
        Cancel a user's subscription.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current subscription
            subscription = self.get_user_subscription(user_id)
            
            if not subscription:
                logger.warning(f"No subscription found to cancel for user {user_id}")
                return False
            
            # Update the subscription status
            query = """
            UPDATE subscriptions
            SET 
                status = 'canceled',
                updated_at = NOW()
            WHERE 
                id = $1
            RETURNING id
            """
            
            result = self.db_client.execute_query(query, [subscription["id"]])
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.error(f"Failed to cancel subscription for user {user_id}")
                return False
            
            logger.info(f"Canceled subscription {subscription['id']} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return False

    def add_paper_credits(self, user_id: str, credits: int) -> bool:
        """
        Add paper credits to a user's account.

        Args:
            user_id: User ID
            credits: Number of credits to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current subscription
            subscription = self.get_user_subscription(user_id)
            
            if not subscription:
                logger.warning(f"No subscription found to add credits for user {user_id}")
                return False
            
            # Update the subscription with additional credits
            current_credits = subscription.get("additional_credits", 0)
            new_credits = current_credits + credits
            
            query = """
            UPDATE subscriptions
            SET 
                additional_credits = $1,
                updated_at = NOW()
            WHERE 
                id = $2
            RETURNING id
            """
            
            result = self.db_client.execute_query(query, [new_credits, subscription["id"]])
            
            if not result or not result.get("data") or len(result["data"]) == 0:
                logger.error(f"Failed to add credits for user {user_id}")
                return False
            
            logger.info(f"Added {credits} credits to user {user_id}, new total: {new_credits}")
            return True
        except Exception as e:
            logger.error(f"Error adding paper credits: {str(e)}")
            return False

    def use_paper_credit(self, user_id: str) -> bool:
        """
        Use a paper credit from a user's account.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current subscription
            subscription = self.get_user_subscription(user_id)
            
            if not subscription:
                logger.warning(f"No subscription found to use credit for user {user_id}")
                return False
            
            # Check if user has enough credits
            papers_limit = subscription.get("papers_limit", 0)
            papers_used = subscription.get("papers_used", 0)
            additional_credits = subscription.get("additional_credits", 0)
            
            # First use monthly credits, then additional credits
            if papers_used < papers_limit:
                # Use a monthly credit
                query = """
                UPDATE subscriptions
                SET 
                    papers_used = papers_used + 1,
                    updated_at = NOW()
                WHERE 
                    id = $1
                RETURNING id
                """
                
                result = self.db_client.execute_query(query, [subscription["id"]])
                
                if not result or not result.get("data") or len(result["data"]) == 0:
                    logger.error(f"Failed to use monthly credit for user {user_id}")
                    return False
                
                logger.info(f"Used monthly credit for user {user_id}, new used: {papers_used + 1}")
                return True
            elif additional_credits > 0:
                # Use an additional credit
                query = """
                UPDATE subscriptions
                SET 
                    additional_credits = additional_credits - 1,
                    updated_at = NOW()
                WHERE 
                    id = $1
                RETURNING id
                """
                
                result = self.db_client.execute_query(query, [subscription["id"]])
                
                if not result or not result.get("data") or len(result["data"]) == 0:
                    logger.error(f"Failed to use additional credit for user {user_id}")
                    return False
                
                logger.info(f"Used additional credit for user {user_id}, new additional: {additional_credits - 1}")
                return True
            else:
                logger.warning(f"User {user_id} has no credits left")
                return False
        except Exception as e:
            logger.error(f"Error using paper credit: {str(e)}")
            return False
