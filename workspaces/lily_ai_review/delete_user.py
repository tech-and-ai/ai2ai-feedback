#!/usr/bin/env python3
"""
Script to safely delete a user by removing all their data from related tables first.
"""

import sys
import logging
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_user(user_id):
    """
    Delete a user and all their related data.
    
    Args:
        user_id: The ID of the user to delete
    """
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check if user exists in auth.users
    try:
        user_response = supabase.from_('auth.users').select('*').eq('id', user_id).execute()
        if not user_response.data or len(user_response.data) == 0:
            logger.error(f"User {user_id} not found in auth.users table")
            return False
        
        logger.info(f"Found user {user_id} in auth.users table")
    except Exception as e:
        logger.error(f"Error checking user in auth.users table: {str(e)}")
        return False
    
    # Delete from saas_job_tracking
    try:
        response = supabase.table("saas_job_tracking").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_job_tracking table")
    except Exception as e:
        logger.error(f"Error deleting from saas_job_tracking table: {str(e)}")
    
    # Delete from saas_notification_logs
    try:
        response = supabase.table("saas_notification_logs").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_notification_logs table")
    except Exception as e:
        logger.error(f"Error deleting from saas_notification_logs table: {str(e)}")
    
    # Delete from saas_paper_credit_usage
    try:
        response = supabase.table("saas_paper_credit_usage").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_paper_credit_usage table")
    except Exception as e:
        logger.error(f"Error deleting from saas_paper_credit_usage table: {str(e)}")
    
    # Delete from saas_paper_credits
    try:
        response = supabase.table("saas_paper_credits").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_paper_credits table")
    except Exception as e:
        logger.error(f"Error deleting from saas_paper_credits table: {str(e)}")
    
    # Delete from saas_papers
    try:
        response = supabase.table("saas_papers").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_papers table")
    except Exception as e:
        logger.error(f"Error deleting from saas_papers table: {str(e)}")
    
    # Delete from saas_user_subscriptions
    try:
        response = supabase.table("saas_user_subscriptions").delete().eq("user_id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_user_subscriptions table")
    except Exception as e:
        logger.error(f"Error deleting from saas_user_subscriptions table: {str(e)}")
    
    # Delete from saas_users
    try:
        response = supabase.table("saas_users").delete().eq("id", user_id).execute()
        logger.info(f"Deleted {len(response.data)} rows from saas_users table")
    except Exception as e:
        logger.error(f"Error deleting from saas_users table: {str(e)}")
    
    # Finally, delete from auth.users using RPC
    try:
        # Use RPC to execute SQL directly
        query = f"DELETE FROM auth.users WHERE id = '{user_id}'"
        response = supabase.rpc('execute_sql', {'query': query}).execute()
        logger.info(f"Deleted user from auth.users table")
        return True
    except Exception as e:
        logger.error(f"Error deleting from auth.users table: {str(e)}")
        return False

def main():
    """Main function to delete a user."""
    if len(sys.argv) != 2:
        print("Usage: python delete_user.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    print(f"Are you sure you want to delete user {user_id} and all their data? (y/n)")
    confirmation = input().strip().lower()
    
    if confirmation != 'y':
        print("Deletion cancelled")
        sys.exit(0)
    
    success = delete_user(user_id)
    
    if success:
        print(f"User {user_id} and all their data have been deleted successfully")
    else:
        print(f"Failed to delete user {user_id}")

if __name__ == '__main__':
    main()
