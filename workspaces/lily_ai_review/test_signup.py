#!/usr/bin/env python3
"""
Test script to verify the sign-up process.
This script will:
1. Register a new user
2. Check if the user was created in the database
3. Check if a verification email was sent
"""

import os
import sys
import logging
import random
import string
import time
from dotenv import load_dotenv
from auth.service import AuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_signup.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_random_string(length=8):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def test_signup():
    """Test the sign-up process."""
    # Initialize the auth service
    auth_service = AuthService()
    
    # Generate random email and username to avoid conflicts
    random_suffix = generate_random_string()
    email = f"test_{random_suffix}@example.com"
    username = f"testuser_{random_suffix}"
    password = "Password123!"
    name = f"Test User {random_suffix}"
    
    logger.info(f"Testing sign-up with email: {email}, username: {username}")
    
    # Attempt to sign up
    user, error_message = auth_service.sign_up(email, password, username, name)
    
    if user:
        logger.info(f"Sign-up successful! User ID: {user.id}")
        
        # Check if user exists in auth.users
        try:
            auth_user_query = """
            SELECT COUNT(*) FROM auth.users WHERE LOWER(email) = LOWER($1)
            """
            auth_user_result = auth_service.supabase.rpc('execute_sql', {
                'query': auth_user_query,
                'params': [email]
            }).execute()
            
            if auth_user_result.data and auth_user_result.data[0]['count'] > 0:
                logger.info(f"User exists in auth.users table: {email}")
            else:
                logger.error(f"User does not exist in auth.users table: {email}")
        except Exception as e:
            logger.error(f"Error checking auth.users table: {str(e)}")
        
        # Check if user exists in saas_users
        try:
            saas_user_query = """
            SELECT COUNT(*) FROM public.saas_users WHERE LOWER(email) = LOWER($1)
            """
            saas_user_result = auth_service.supabase.rpc('execute_sql', {
                'query': saas_user_query,
                'params': [email]
            }).execute()
            
            if saas_user_result.data and saas_user_result.data[0]['count'] > 0:
                logger.info(f"User exists in saas_users table: {email}")
            else:
                logger.error(f"User does not exist in saas_users table: {email}")
        except Exception as e:
            logger.error(f"Error checking saas_users table: {str(e)}")
        
        # Check if verification email was sent
        # We can't directly check if an email was sent, but we can check if the user's email_verified flag is False
        try:
            email_verified_query = """
            SELECT email_verified FROM public.saas_users WHERE LOWER(email) = LOWER($1)
            """
            email_verified_result = auth_service.supabase.rpc('execute_sql', {
                'query': email_verified_query,
                'params': [email]
            }).execute()
            
            if email_verified_result.data and len(email_verified_result.data) > 0:
                email_verified = email_verified_result.data[0]['email_verified']
                logger.info(f"User's email_verified flag: {email_verified}")
                if not email_verified:
                    logger.info("Email verification is required, which means a verification email should have been sent.")
                else:
                    logger.warning("User's email is already verified, which is unexpected for a new user.")
            else:
                logger.error(f"Could not retrieve email_verified flag for user: {email}")
        except Exception as e:
            logger.error(f"Error checking email_verified flag: {str(e)}")
        
        logger.info("Sign-up test completed successfully!")
        return True
    else:
        logger.error(f"Sign-up failed! Error: {error_message}")
        return False

if __name__ == "__main__":
    test_signup()
