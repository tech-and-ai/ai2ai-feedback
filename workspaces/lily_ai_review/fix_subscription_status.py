#!/usr/bin/env python
"""
Script to directly update a user's subscription status in the database and session.
This is a one-time fix for users who have subscribed but their status isn't showing correctly.
"""
import os
import sys
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from app.utils.supabase_client import get_supabase_client
from app.services.billing.subscription_service import SubscriptionService

def update_user_subscription(user_id, tier="premium"):
    """
    Update a user's subscription to premium directly in the database.
    
    Args:
        user_id: The user ID to update
        tier: The subscription tier to set (default: premium)
    """
    print(f"Updating user {user_id} to {tier} tier...")
    
    # Get the Supabase client
    supabase = get_supabase_client()
    
    # Create a subscription service
    subscription_service = SubscriptionService()
    
    try:
        # 1. Update the subscription in saas_user_subscriptions
        subscription_id = f"sub_fix_{int(datetime.now().timestamp())}"
        customer_id = f"cus_fix_{int(datetime.now().timestamp())}"
        
        # Update or create the subscription
        subscription_service.update_subscription(
            user_id=user_id,
            tier=tier,
            status="active",
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            papers_limit=10 if tier == "premium" else 1
        )
        print(f"Updated subscription in saas_user_subscriptions table")
        
        # 2. Update the user's subscription tier in saas_users
        try:
            supabase.table("saas_users").upsert({
                "id": user_id,
                "subscription_tier": tier,
                "updated_at": datetime.now().isoformat()
            }).execute()
            print(f"Updated user in saas_users table")
        except Exception as e:
            print(f"Error updating saas_users table: {str(e)}")
            
        # 3. Update the user's metadata in auth.users if possible
        try:
            # This requires admin privileges, so it might fail
            response = supabase.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": {"subscription_tier": tier}}
            )
            print(f"Updated user metadata in auth.users table")
        except Exception as e:
            print(f"Error updating auth.users table (this is expected without admin privileges): {str(e)}")
            
        print(f"Successfully updated user {user_id} to {tier} tier")
        return True
    except Exception as e:
        print(f"Error updating subscription: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_subscription_status.py <user_id> [tier]")
        sys.exit(1)
        
    user_id = sys.argv[1]
    tier = sys.argv[2] if len(sys.argv) > 2 else "premium"
    
    success = update_user_subscription(user_id, tier)
    if success:
        print(f"Successfully updated user {user_id} to {tier} tier")
    else:
        print(f"Failed to update user {user_id}")
