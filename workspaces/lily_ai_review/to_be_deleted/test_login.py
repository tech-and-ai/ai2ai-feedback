#!/usr/bin/env python3
"""
Script to test login with specific credentials.
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

def test_login(email: str, password: str) -> bool:
    """
    Test login with specific credentials.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        bool: True if login is successful, False otherwise
    """
    supabase = get_supabase_client()
    
    try:
        # Try to sign in with the email and password
        logger.info(f"Attempting to sign in with email: {email}")
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Check if sign in was successful
        if response and hasattr(response, 'user') and response.user:
            logger.info(f"Sign in successful for user: {response.user.id}")
            logger.info(f"User email: {response.user.email}")
            logger.info(f"User metadata: {response.user.user_metadata}")
            return True
        else:
            logger.error("Sign in response did not contain user data")
            return False
    except Exception as e:
        logger.error(f"Sign in error: {str(e)}")
        return False

def main():
    """
    Main function.
    """
    if len(sys.argv) < 3:
        logger.error("Please provide email and password")
        print("Usage: python test_login.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    logger.info(f"Testing login for email: {email}")
    
    success = test_login(email, password)
    
    if success:
        logger.info(f"Login successful for {email}")
    else:
        logger.error(f"Login failed for {email}")

if __name__ == "__main__":
    main()
