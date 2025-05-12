#!/usr/bin/env python3
"""
Script to create a user directly through Supabase admin API.
This bypasses email verification and rate limits.
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

def create_user(email: str, password: str, username: str, name: str = None) -> bool:
    """
    Create a user directly through Supabase admin API.
    
    Args:
        email: User's email address
        password: User's password
        username: User's username
        name: User's full name (optional)
        
    Returns:
        bool: True if user was created successfully, False otherwise
    """
    supabase = get_supabase_client()
    
    try:
        # Create user metadata
        user_metadata = {
            "username": username,
            "name": name or username,
            "subscription_tier": "free"
        }
        
        # Create the user through admin API
        logger.info(f"Creating user with email: {email}")
        
        # First check if user already exists
        try:
            # Try to create user with admin API
            response = supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,  # Skip email verification
                "user_metadata": user_metadata
            })
            
            if hasattr(response, 'user') and response.user:
                user_id = response.user.id
                logger.info(f"User created successfully with ID: {user_id}")
                
                # Create entry in saas_users table
                try:
                    logger.info(f"Creating entry in saas_users table for user: {user_id}")
                    result = supabase.table('saas_users').insert({
                        'id': user_id,
                        'username': username,
                        'email': email,
                        'name': name or username,
                        'subscription_tier': 'free',
                        'email_verified': True
                    }).execute()
                    
                    logger.info(f"Entry created in saas_users table: {result.data}")
                    return True
                except Exception as db_error:
                    logger.error(f"Error creating entry in saas_users table: {str(db_error)}")
                    # Continue anyway since the auth user was created
                    return True
            else:
                logger.error("User creation response did not contain user data")
                return False
                
        except Exception as e:
            if "user already exists" in str(e).lower():
                logger.warning(f"User with email {email} already exists")
                return False
            else:
                logger.error(f"Error creating user: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False

def main():
    """
    Main function.
    """
    if len(sys.argv) < 4:
        logger.error("Please provide email, password, and username")
        print("Usage: python create_admin_user.py <email> <password> <username> [name]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    username = sys.argv[3]
    name = sys.argv[4] if len(sys.argv) > 4 else None
    
    logger.info(f"Creating user: {email}, username: {username}")
    
    success = create_user(email, password, username, name)
    
    if success:
        logger.info(f"User {email} created successfully")
    else:
        logger.error(f"Failed to create user {email}")

if __name__ == "__main__":
    main()
