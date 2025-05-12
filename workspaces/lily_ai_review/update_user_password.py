#!/usr/bin/env python
"""
Script to update a user's password directly in the database.
"""
import os
import sys
import logging
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_user_password(email, password):
    """
    Update a user's password directly in the database.
    
    Args:
        email: The email address of the user
        password: The new password for the user
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Check if user exists
        response = supabase.table('saas_users').select('*').eq('email', email).execute()
        
        if not response.data or len(response.data) == 0:
            logger.error(f"User with email {email} not found")
            return False
        
        # Get the user ID
        user_id = response.data[0]['id']
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update the password in the saas_users table
        update_response = supabase.table('saas_users').update({
            'password_hash': password_hash,
            'updated_at': datetime.now().isoformat()
        }).eq('id', user_id).execute()
        
        logger.info(f"Updated password for user {email} in saas_users table")
        
        # Try to update the password in the auth.users table as well
        try:
            # This might fail if we don't have admin access to the auth.users table
            auth_update = supabase.rpc('update_user_password', {
                'user_id': user_id,
                'password': password
            }).execute()
            
            logger.info(f"Updated password for user {email} in auth.users table")
        except Exception as auth_error:
            logger.warning(f"Could not update password in auth.users table: {str(auth_error)}")
            # Continue anyway since we updated the password in saas_users
        
        return True
    except Exception as e:
        logger.error(f"Error updating user password: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_user_password.py <email> <password>")
        sys.exit(1)
        
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Validate password
    if len(password) < 8:
        print("Password must be at least 8 characters long")
        sys.exit(1)
        
    # Update the user's password
    success = update_user_password(email, password)
    
    if success:
        print(f"Password updated successfully for user {email}")
        sys.exit(0)
    else:
        print(f"Failed to update password for user {email}")
        sys.exit(1)
