"""
Supabase client module for AI-to-AI Feedback API

This module provides a client for interacting with the Supabase database.
"""

import os
import uuid
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL and key from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if Supabase URL and key are set
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or key not set in environment variables")

# Set up headers for Supabase REST API
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY
}

class SupabaseClient:
    """Client for interacting with the Supabase database"""

    @staticmethod
    def create_session(
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_multi_agent: bool = False
    ) -> Optional[str]:
        """
        Create a new session
        
        Args:
            session_id: Optional session ID (generated if not provided)
            system_prompt: Optional system prompt
            title: Optional title
            tags: Optional list of tags
            is_multi_agent: Whether this is a multi-agent session
            
        Returns:
            Optional[str]: Session ID if successful, None otherwise
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Format tags
            tags_str = ",".join(tags) if tags else ""
            
            # Call the create_ai_agent_session function
            url = f"{SUPABASE_URL}/rest/v1/rpc/create_ai_agent_session"
            data = {
                "p_id": session_id,
                "p_system_prompt": system_prompt,
                "p_title": title,
                "p_tags": tags_str,
                "p_is_multi_agent": is_multi_agent
            }
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return session_id
            else:
                print(f"Error creating session: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating session: {str(e)}")
            return None

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data if found, None otherwise
        """
        try:
            # Call the get_ai_agent_session function
            url = f"{SUPABASE_URL}/rest/v1/rpc/get_ai_agent_session"
            response = requests.post(url, headers=headers, json={"p_id": session_id})
            
            if response.status_code == 200 and response.json():
                # The response is a list with one item
                return response.json()[0]
            else:
                print(f"Session not found: {session_id} - {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting session: {str(e)}")
            return None

    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        agent_id: Optional[int] = None,
        initiator: Optional[str] = None
    ) -> Optional[int]:
        """
        Add a message to a session
        
        Args:
            session_id: Session ID
            role: Message role (system, user, assistant, agent)
            content: Message content
            agent_id: Optional agent ID
            initiator: Optional initiator (user or agent index)
            
        Returns:
            Optional[int]: Message ID if successful, None otherwise
        """
        # TODO: Implement this function
        # Need to create a stored procedure in Supabase
        return None

    @staticmethod
    def add_feedback(
        message_id: int,
        feedback_text: str,
        structured: Dict[str, str],
        source_model: str
    ) -> Optional[int]:
        """
        Add feedback for a message
        
        Args:
            message_id: Message ID
            feedback_text: Full feedback text
            structured: Structured feedback components
            source_model: Source model
            
        Returns:
            Optional[int]: Feedback ID if successful, None otherwise
        """
        # TODO: Implement this function
        # Need to create a stored procedure in Supabase
        return None

# Example usage
if __name__ == "__main__":
    # Create a session
    session_id = SupabaseClient.create_session(
        system_prompt="Example system prompt",
        title="Example Session",
        tags=["example", "test"],
        is_multi_agent=False
    )
    
    if session_id:
        print(f"Created session: {session_id}")
        
        # Get the session
        session = SupabaseClient.get_session(session_id)
        
        if session:
            print(f"Retrieved session: {json.dumps(session, indent=2)}")
        else:
            print("Failed to retrieve session")
