"""
Database client module for Supabase.

This module provides a singleton client for interacting with Supabase.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Union
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseClient:
    """
    Singleton database client for Supabase.
    """
    _instance: Optional['DatabaseClient'] = None
    _client: Optional[Client] = None

    def __new__(cls) -> 'DatabaseClient':
        """
        Create a new instance of the DatabaseClient if one doesn't exist.

        Returns:
            The singleton instance of DatabaseClient
        """
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the Supabase client."""
        try:
            supabase_url = os.getenv("SUPABASE_PROJECT_URL")
            supabase_key = os.getenv("SUPABASE_API_KEY")

            if not supabase_url or not supabase_key:
                logger.error("SUPABASE_PROJECT_URL or SUPABASE_API_KEY environment variables not set")
                raise ValueError("Supabase credentials not found in environment variables")

            self._client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """
        Get the Supabase client.

        Returns:
            The Supabase client

        Raises:
            RuntimeError: If the client is not initialized
        """
        if self._client is None:
            logger.error("Supabase client not initialized")
            raise RuntimeError("Supabase client not initialized")
        return self._client

    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.

        Args:
            query: The SQL query to execute
            params: Query parameters (optional)

        Returns:
            The query results

        Raises:
            Exception: If the query fails
        """
        try:
            # For now, let's use a direct table query instead of RPC
            # This is a temporary solution until we set up the proper RPC function
            if "SELECT" in query.upper():
                # For SELECT queries, use the REST API
                table_name = self._extract_table_name(query)
                if table_name:
                    # Use a simple filter for now
                    if "WHERE" in query.upper() and params and len(params) > 0:
                        # Extract the column name from the WHERE clause
                        column_name = self._extract_column_name(query)
                        if column_name:
                            response = self.client.table(table_name).select("*").eq(column_name, params[0]).execute()
                            if hasattr(response, 'data'):
                                return response.data
                    else:
                        # No WHERE clause, just select all
                        response = self.client.table(table_name).select("*").execute()
                        if hasattr(response, 'data'):
                            return response.data

            # For other queries, log that we can't execute them yet
            logger.warning(f"Complex query execution not implemented yet: {query}")
            return []
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            return []

    def _extract_table_name(self, query: str) -> Optional[str]:
        """
        Extract the table name from a SQL query.

        Args:
            query: The SQL query

        Returns:
            The table name or None if not found
        """
        # This is a very simple parser and won't work for complex queries
        import re
        match = re.search(r'FROM\s+([a-zA-Z0-9_.]+)', query, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            # Remove schema prefix if present
            if '.' in table_name:
                schema, table = table_name.split('.')
                return table
            return table_name
        return None

    def _extract_column_name(self, query: str) -> Optional[str]:
        """
        Extract the column name from a WHERE clause.

        Args:
            query: The SQL query

        Returns:
            The column name or None if not found
        """
        # This is a very simple parser and won't work for complex queries
        import re
        match = re.search(r'WHERE\s+([a-zA-Z0-9_.]+)\s*=', query, re.IGNORECASE)
        if match:
            column_name = match.group(1)
            # Remove table prefix if present
            if '.' in column_name:
                table, column = column_name.split('.')
                return column
            return column_name
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID from auth.users.

        Args:
            user_id: The user ID

        Returns:
            The user data or None if not found
        """
        try:
            query = "SELECT * FROM auth.users WHERE id = $1"
            result = self.execute_query(query, [user_id])

            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by email from auth.users.

        Args:
            email: The user's email

        Returns:
            The user data or None if not found
        """
        try:
            query = "SELECT * FROM auth.users WHERE email = $1"
            result = self.execute_query(query, [email])

            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username from auth.users metadata.

        Args:
            username: The username

        Returns:
            The user data or None if not found
        """
        try:
            query = """
            SELECT * FROM auth.users
            WHERE raw_user_meta_data->>'username' = $1
            """
            result = self.execute_query(query, [username])

            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None

    def update_user_metadata(self, user_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update a user's metadata.

        Args:
            user_id: The user ID
            metadata: The metadata to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current metadata
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            # Merge with existing metadata
            current_metadata = user.get('raw_user_meta_data', {}) or {}
            if isinstance(current_metadata, str):
                current_metadata = json.loads(current_metadata)

            # Update metadata
            updated_metadata = {**current_metadata, **metadata}

            # Convert to JSON string for SQL
            metadata_json = json.dumps(updated_metadata)

            # Update the user's metadata
            query = """
            UPDATE auth.users
            SET raw_user_meta_data = $1::jsonb
            WHERE id = $2
            """
            self.execute_query(query, [metadata_json, user_id])

            return True
        except Exception as e:
            logger.error(f"Error updating user metadata: {str(e)}")
            return False

    def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's subscription.

        Args:
            user_id: The user ID

        Returns:
            The subscription data or None if not found
        """
        try:
            query = """
            SELECT * FROM lily_subscriptions
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """
            result = self.execute_query(query, [user_id])

            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error getting subscription: {str(e)}")
            return None

# Create a singleton instance
db_client = DatabaseClient()

def get_db_client() -> DatabaseClient:
    """
    Get the database client singleton.

    Returns:
        The database client
    """
    return db_client
