"""
Database client module for Supabase.

This module provides a singleton client for interacting with Supabase.
"""

import os
import logging
from typing import Optional, Dict, Any, List
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
            if params:
                response = self.client.rpc('execute_sql', {'query': query, 'params': params}).execute()
            else:
                response = self.client.rpc('execute_sql', {'query': query}).execute()
                
            if hasattr(response, 'data'):
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            raise

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
                import json
                current_metadata = json.loads(current_metadata)
                
            # Update metadata
            updated_metadata = {**current_metadata, **metadata}
            
            # Convert to JSON string for SQL
            import json
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

# Create a singleton instance
db_client = DatabaseClient()

def get_db_client() -> DatabaseClient:
    """
    Get the database client singleton.
    
    Returns:
        The database client
    """
    return db_client
