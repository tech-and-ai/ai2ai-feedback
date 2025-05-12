#!/usr/bin/env python
"""
Script to reset the admin user's password.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from auth.service import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def reset_admin_password(new_password):
    """
    Reset the admin user's password.
    
    Args:
        new_password: The new password to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize auth service
        auth_service = AuthService()
        
        # Admin user ID
        admin_user_id = "55b4ec8c-2cf5-40fe-8718-75fe45f49a69"
        
        # Update the password
        success = auth_service.update_password(admin_user_id, new_password)
        
        if success:
            logger.info(f"Successfully reset password for admin user (ID: {admin_user_id})")
            return True
        else:
            logger.error(f"Failed to reset password for admin user (ID: {admin_user_id})")
            return False
    except Exception as e:
        logger.error(f"Error resetting admin password: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reset_admin_password.py <new_password>")
        sys.exit(1)
        
    new_password = sys.argv[1]
    
    # Validate password
    if len(new_password) < 8:
        print("Password must be at least 8 characters long")
        sys.exit(1)
        
    # Reset the password
    success = reset_admin_password(new_password)
    
    if success:
        print("Admin password reset successfully")
        sys.exit(0)
    else:
        print("Failed to reset admin password")
        sys.exit(1)
