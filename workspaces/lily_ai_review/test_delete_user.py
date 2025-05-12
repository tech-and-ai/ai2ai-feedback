#!/usr/bin/env python3
"""
Script to test deleting a user and capture the exact error message.
"""

import sys
import os
import logging
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_delete_user(user_id):
    """
    Test deleting a user and capture the exact error message.
    
    Args:
        user_id: The ID of the user to delete
    """
    # Get Supabase URL and service key from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables not set")
        return False
    
    # Set up headers with the service key
    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    # First, try to delete the user using the Admin API
    try:
        admin_url = f"{supabase_url}/auth/v1/admin/users/{user_id}"
        logger.info(f"Attempting to delete user {user_id} using Admin API: {admin_url}")
        
        response = requests.delete(admin_url, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully deleted user {user_id} using Admin API")
            return True
        else:
            logger.error(f"Failed to delete user using Admin API: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
            # Try to parse the error message
            try:
                error_data = response.json()
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
    except Exception as e:
        logger.error(f"Error using Admin API: {str(e)}")
    
    # If that fails, try to delete directly from auth.users using SQL
    try:
        sql_url = f"{supabase_url}/rest/v1/rpc/execute_sql"
        logger.info(f"Attempting to delete user {user_id} using SQL")
        
        sql_query = f"DELETE FROM auth.users WHERE id = '{user_id}'"
        payload = {"query": sql_query}
        
        response = requests.post(sql_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            logger.info(f"Successfully deleted user {user_id} using SQL")
            return True
        else:
            logger.error(f"Failed to delete user using SQL: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
            # Try to parse the error message
            try:
                error_data = response.json()
                logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
    except Exception as e:
        logger.error(f"Error using SQL: {str(e)}")
    
    # If both methods fail, try to identify the specific constraint causing the issue
    try:
        logger.info("Attempting to identify the constraint causing the issue")
        
        # Get all tables that might reference auth.users
        tables_query = """
        SELECT table_schema, table_name, column_name
        FROM information_schema.columns
        WHERE column_name = 'user_id'
        AND table_schema NOT IN ('pg_catalog', 'information_schema')
        """
        
        payload = {"query": tables_query}
        response = requests.post(sql_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            tables_data = response.json()
            logger.info(f"Found {len(tables_data)} tables with user_id column")
            
            # For each table, check if it has data for this user
            for table_info in tables_data:
                schema = table_info.get('table_schema', 'public')
                table = table_info.get('table_name')
                
                if schema and table:
                    count_query = f"""
                    SELECT COUNT(*) FROM {schema}.{table} WHERE user_id = '{user_id}'
                    """
                    
                    payload = {"query": count_query}
                    count_response = requests.post(sql_url, headers=headers, json=payload)
                    
                    if count_response.status_code == 200:
                        count_data = count_response.json()
                        count = count_data[0].get('count', 0) if count_data else 0
                        
                        if count > 0:
                            logger.info(f"Found {count} rows in {schema}.{table} for user {user_id}")
                            
                            # Try to delete these rows
                            delete_query = f"""
                            DELETE FROM {schema}.{table} WHERE user_id = '{user_id}'
                            """
                            
                            payload = {"query": delete_query}
                            delete_response = requests.post(sql_url, headers=headers, json=payload)
                            
                            if delete_response.status_code == 200:
                                logger.info(f"Successfully deleted rows from {schema}.{table}")
                            else:
                                logger.error(f"Failed to delete rows from {schema}.{table}: {delete_response.status_code}")
                                logger.error(f"Response: {delete_response.text}")
        else:
            logger.error(f"Failed to get tables: {response.status_code}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error identifying constraint: {str(e)}")
    
    return False

def main():
    """Main function to test deleting a user."""
    if len(sys.argv) != 2:
        print("Usage: python test_delete_user.py <user_id>")
        sys.exit(1)
    
    user_id = sys.argv[1]
    
    print(f"Testing deletion of user {user_id}")
    success = test_delete_user(user_id)
    
    if success:
        print(f"Successfully deleted user {user_id}")
    else:
        print(f"Failed to delete user {user_id}")

if __name__ == '__main__':
    main()
