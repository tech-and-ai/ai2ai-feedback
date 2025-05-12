#!/usr/bin/env python3
"""
Script to list all users in the database.
"""

import os
import logging
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_users():
    """List all users in the database."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Get users from saas_users table
    try:
        response = supabase.table("saas_users").select("*").execute()
        
        if response.data:
            print(f"\nFound {len(response.data)} users in saas_users table:")
            for user in response.data:
                print(f"ID: {user.get('id')}")
                print(f"Username: {user.get('username')}")
                print(f"Email: {user.get('email')}")
                print(f"Created At: {user.get('created_at')}")
                print("-" * 50)
        else:
            print("No users found in saas_users table.")
    except Exception as e:
        logger.error(f"Error getting users from saas_users table: {str(e)}")
    
    # Get users from auth.users table using SQL
    try:
        query = """
        SELECT 
            id, 
            email, 
            created_at
        FROM 
            auth.users
        """
        
        response = supabase.rpc('execute_sql', {'query': query}).execute()
        
        if response.data:
            print(f"\nFound {len(response.data)} users in auth.users table:")
            for user in response.data:
                if isinstance(user, dict):
                    print(f"ID: {user.get('id')}")
                    print(f"Email: {user.get('email')}")
                    print(f"Created At: {user.get('created_at')}")
                    print("-" * 50)
                else:
                    print(f"User data: {user}")
        else:
            print("No users found in auth.users table.")
    except Exception as e:
        logger.error(f"Error getting users from auth.users table: {str(e)}")

if __name__ == '__main__':
    list_users()
