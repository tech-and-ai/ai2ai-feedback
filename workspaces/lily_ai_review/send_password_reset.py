#!/usr/bin/env python
"""
Script to send a password reset email to a user.
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

def send_password_reset(email):
    """
    Send a password reset email to the specified user.
    
    Args:
        email: The email address of the user
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Supabase client
        supabase = get_supabase_client()
        
        # Send password reset email
        response = supabase.auth.reset_password_email(email)
        
        logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python send_password_reset.py <email>")
        sys.exit(1)
        
    email = sys.argv[1]
    
    # Send the password reset email
    success = send_password_reset(email)
    
    if success:
        print(f"Password reset email sent to {email}")
        sys.exit(0)
    else:
        print(f"Failed to send password reset email to {email}")
        sys.exit(1)
