#!/usr/bin/env python3
"""
Script to delete a user directly using the Supabase admin API.
"""

import sys
import os
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_user(user_id):
    """
    Delete a user using the Supabase admin API.

    Args:
        user_id: The ID of the user to delete
    """
    # Get Supabase URL and service key from environment variables
    supabase_url = os.getenv("SUPABASE_PROJECT_URL")
    supabase_service_key = os.getenv("SUPABASE_API_KEY")

    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_PROJECT_URL or SUPABASE_API_KEY environment variables not set")
        return False

    # Set up headers with the service key
    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # List of tables to clean up
    tables = [
        "saas_job_tracking",
        "saas_notification_logs",
        "saas_paper_credit_usage",
        "saas_paper_credits",
        "saas_papers",
        "saas_user_subscriptions",
        "saas_users"
    ]

    # Delete data from each table
    for table in tables:
        try:
            # Construct the URL for the DELETE request
            if table == "saas_users":
                url = f"{supabase_url}/rest/v1/{table}?id=eq.{user_id}"
            else:
                url = f"{supabase_url}/rest/v1/{table}?user_id=eq.{user_id}"

            logger.info(f"Deleting data from {table} for user {user_id}...")

            # Make the DELETE request
            response = requests.delete(url, headers=headers)

            # Check if the request was successful
            if response.status_code in [200, 204]:
                logger.info(f"Successfully deleted data from {table}")
            else:
                logger.error(f"Failed to delete data from {table}: {response.status_code}")
                logger.error(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"Error deleting data from {table}: {str(e)}")

    # Try to execute a direct SQL query to delete from auth.users
    try:
        logger.info("Attempting to delete user with direct SQL...")

        sql_url = f"{supabase_url}/rest/v1/rpc/execute_sql"
        sql_query = f"DELETE FROM auth.users WHERE id = '{user_id}'"
        payload = {"query": sql_query}

        response = requests.post(sql_url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info(f"Successfully deleted user {user_id} using SQL")
            return True
        else:
            logger.error(f"Failed to delete user using SQL: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error using SQL: {str(e)}")

    # If SQL fails, try the admin API
    try:
        # Construct the URL for the DELETE request to the admin API
        url = f"{supabase_url}/auth/v1/admin/users/{user_id}"

        logger.info(f"Attempting to delete user {user_id} using Admin API...")

        # Make the DELETE request
        response = requests.delete(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"Successfully deleted user {user_id} from auth.users table")
            return True
        else:
            logger.error(f"Failed to delete user from auth.users table: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error deleting from auth.users table: {str(e)}")
        return False

def main():
    """Main function to delete a user."""
    if len(sys.argv) != 2:
        print("Usage: python delete_user_direct.py <user_id>")
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
