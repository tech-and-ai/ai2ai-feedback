#!/usr/bin/env python
"""
Script to update a user's password in the auth.users table using the admin API.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_auth_password(email, password):
    """
    Update a user's password in the auth.users table using the admin API.
    
    Args:
        email: The email address of the user
        password: The new password for the user
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Get the user by email
        users = supabase.auth.admin.list_users()
        
        # Find the user with the matching email
        user_id = None
        for user in users:
            if hasattr(user, 'email') and user.email == email:
                user_id = user.id
                break
        
        if not user_id:
            logger.error(f"User with email {email} not found in auth.users table")
            return False
        
        # Update the user's password
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"password": password}
        )
        
        logger.info(f"Updated password for user {email} in auth.users table")
        return True
    except Exception as e:
        logger.error(f"Error updating auth password: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_auth_password.py <email> <password>")
        sys.exit(1)
        
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Validate password
    if len(password) < 8:
        print("Password must be at least 8 characters long")
        sys.exit(1)
        
    # Update the user's password
    success = update_auth_password(email, password)
    
    if success:
        print(f"Auth password updated successfully for user {email}")
        sys.exit(0)
    else:
        print(f"Failed to update auth password for user {email}")
        sys.exit(1)
