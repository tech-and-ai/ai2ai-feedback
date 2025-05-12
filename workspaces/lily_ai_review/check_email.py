#!/usr/bin/env python3
"""
Script to check if an email exists in the Supabase auth system.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project directory to the path so we can import from it
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the Supabase client from the project
from app.utils.supabase_client import get_supabase_client

def check_email_exists(email: str) -> bool:
    """
    Check if an email exists in the Supabase auth system.

    Args:
        email: Email address to check

    Returns:
        bool: True if email exists, False otherwise
    """
    supabase = get_supabase_client()

    try:
        # Try to get user by email
        response = supabase.auth.admin.list_users()

        # The response format might vary, so let's handle different possibilities
        users = []
        if hasattr(response, 'users'):
            users = response.users
        elif isinstance(response, list):
            users = response
        elif hasattr(response, 'data') and isinstance(response.data, list):
            users = response.data

        # Log the response for debugging
        logger.info(f"Found {len(users)} users in the system")

        # Check if the email exists in the list of users
        for user in users:
            # Handle different user object formats
            user_email = None
            if hasattr(user, 'email'):
                user_email = user.email
            elif isinstance(user, dict) and 'email' in user:
                user_email = user['email']

            if user_email:
                logger.info(f"User: {user_email}")
                if user_email.lower() == email.lower():
                    logger.info(f"Found user with email: {email}")
                    return True

        # If we didn't find the user, try a direct query
        try:
            # Try to query the auth.users table directly
            logger.info("Trying direct query to auth.users table")
            result = supabase.table('auth.users').select('email').eq('email', email.lower()).execute()
            if result and hasattr(result, 'data') and len(result.data) > 0:
                logger.info(f"Found user with email via direct query: {email}")
                return True
        except Exception as e:
            logger.warning(f"Direct query failed: {str(e)}")

        logger.info(f"No user found with email: {email}")
        return False
    except Exception as e:
        logger.error(f"Error checking email: {str(e)}")
        return False

def main():
    """
    Main function.
    """
    if len(sys.argv) < 2:
        logger.error("Please provide an email address to check")
        sys.exit(1)

    email = sys.argv[1]
    logger.info(f"Checking if email exists: {email}")

    exists = check_email_exists(email)

    if exists:
        logger.info(f"Email {email} exists in the system")
    else:
        logger.info(f"Email {email} does not exist in the system")

if __name__ == "__main__":
    main()
