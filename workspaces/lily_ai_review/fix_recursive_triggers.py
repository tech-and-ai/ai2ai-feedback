#!/usr/bin/env python
"""
Script to fix the recursive trigger issue in the Supabase database.

This script uses direct SQL queries to update user information safely without
triggering the recursive triggers between auth.users and auth.saas_users tables.
"""
import os
import logging
import argparse
import json
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase project ID
PROJECT_ID = "brxpkhpkitfzecvmwzgz"

def get_supabase_api_key():
    """
    Get the Supabase API key from environment variables.

    Returns:
        str: The Supabase API key
    """
    api_key = (
        os.getenv("SUPABASE_KEY") or
        os.getenv("SUPABASE_API_KEY") or
        os.getenv("SUPABASE_SERVICE_KEY")
    )

    if not api_key:
        logger.warning("No Supabase API key found in environment variables.")
        api_key = input("Enter your Supabase API key: ")

    return api_key

def execute_query(query, params=None):
    """
    Execute a SQL query using the Supabase Management API.

    Args:
        query (str): The SQL query to execute
        params (dict, optional): The parameters for the query

    Returns:
        dict: The response from the API
    """
    api_key = get_supabase_api_key()

    url = f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "query": query
    }

    if params:
        data["params"] = params

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        logger.error(f"Error executing query: {response.text}")
        raise Exception(f"Error executing query: {response.text}")

    return response.json()

def update_user_safely(user_id, email=None, password=None, user_metadata=None):
    """
    Update a user's information safely using direct SQL queries.

    Args:
        user_id: The user's ID
        email: The new email address (optional)
        password: The new password (optional)
        user_metadata: The new user metadata (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Build the query
        query = f"SELECT public.safe_update_users('{user_id}'"

        if email:
            query += f", '{email}'"
        else:
            query += ", NULL"

        if password:
            query += f", '{password}'"
        else:
            query += ", NULL"

        if user_metadata:
            query += f", '{json.dumps(user_metadata)}'::jsonb"
        else:
            query += ", NULL"

        query += ");"

        # Execute the query
        result = execute_query(query)

        logger.info(f"Successfully updated user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        return False

def list_users():
    """
    List all users in the database.

    Returns:
        List of users
    """
    try:
        # Query users directly from the database
        query = """
        SELECT id, email, raw_user_meta_data
        FROM auth.users
        ORDER BY created_at DESC
        """

        # Execute the query
        result = execute_query(query)

        return result.get("data", [])
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return []

def fix_recursive_triggers():
    """
    Fix the recursive triggers issue by creating a function to safely update users.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a function to safely update users without triggering recursive triggers
        create_function_query = """
        CREATE OR REPLACE FUNCTION public.safe_update_users(
            p_user_id UUID,
            p_email TEXT DEFAULT NULL,
            p_password TEXT DEFAULT NULL,
            p_user_metadata JSONB DEFAULT NULL
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_result BOOLEAN := FALSE;
            v_encrypted_password TEXT;
        BEGIN
            -- Set session variable to disable triggers
            SET LOCAL session_replication_role = 'replica';

            -- Update auth.users table
            IF p_email IS NOT NULL OR p_password IS NOT NULL OR p_user_metadata IS NOT NULL THEN
                UPDATE auth.users
                SET
                    email = COALESCE(p_email, email),
                    encrypted_password = CASE
                        WHEN p_password IS NOT NULL THEN
                            crypt(p_password, gen_salt('bf'))
                        ELSE
                            encrypted_password
                        END,
                    raw_user_meta_data = CASE
                        WHEN p_user_metadata IS NOT NULL THEN
                            p_user_metadata
                        ELSE
                            raw_user_meta_data
                        END,
                    updated_at = NOW()
                WHERE id = p_user_id;

                -- Get the encrypted password if it was updated
                IF p_password IS NOT NULL THEN
                    SELECT encrypted_password INTO v_encrypted_password
                    FROM auth.users
                    WHERE id = p_user_id;
                END IF;

                -- Update auth.saas_users table
                UPDATE auth.saas_users
                SET
                    email = COALESCE(p_email, email),
                    encrypted_password = CASE
                        WHEN p_password IS NOT NULL THEN
                            v_encrypted_password
                        ELSE
                            encrypted_password
                        END,
                    raw_user_meta_data = CASE
                        WHEN p_user_metadata IS NOT NULL THEN
                            p_user_metadata
                        ELSE
                            raw_user_meta_data
                        END,
                    updated_at = NOW()
                WHERE id = p_user_id;

                v_result := TRUE;
            END IF;

            -- Reset session variable
            RESET session_replication_role;

            RETURN v_result;
        END;
        $$ LANGUAGE plpgsql;
        """

        # Execute the query
        execute_query(create_function_query)

        logger.info("Successfully created safe_update_users function")
        return True
    except Exception as e:
        logger.error(f"Error creating safe_update_users function: {str(e)}")
        return False

def main():
    """
    Main function to run the script.
    """
    parser = argparse.ArgumentParser(description='Fix recursive trigger issue in Supabase database')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List users command
    list_parser = subparsers.add_parser('list', help='List all users')

    # Update user command
    update_parser = subparsers.add_parser('update', help='Update a user')
    update_parser.add_argument('--user-id', required=True, help='User ID to update')
    update_parser.add_argument('--email', help='New email address')
    update_parser.add_argument('--password', help='New password')
    update_parser.add_argument('--metadata', help='New user metadata (JSON string)')

    # Fix triggers command
    fix_parser = subparsers.add_parser('fix', help='Fix recursive triggers')

    args = parser.parse_args()

    if args.command == 'list':
        users = list_users()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user['id']}, Email: {user['email']}")

    elif args.command == 'update':
        # Parse metadata if provided
        metadata = None
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                logger.error("Invalid JSON for metadata")
                return False

        # Update the user
        success = update_user_safely(
            args.user_id,
            email=args.email,
            password=args.password,
            user_metadata=metadata
        )

        if success:
            print(f"Successfully updated user {args.user_id}")
        else:
            print(f"Failed to update user {args.user_id}")

    elif args.command == 'fix':
        success = fix_recursive_triggers()
        if success:
            print("Successfully fixed recursive triggers")
        else:
            print("Failed to fix recursive triggers")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
