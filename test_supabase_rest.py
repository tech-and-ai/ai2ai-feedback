"""
Test script to verify the Supabase REST API connection and basic operations.
"""

import os
import uuid
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL and key from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Check if Supabase URL and key are set
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase URL or key not set in environment variables")
    exit(1)

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {SUPABASE_KEY[:5]}...{SUPABASE_KEY[-5:]}")

# Set up headers for Supabase REST API
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY
}

def test_connection():
    """Test the connection to Supabase"""
    try:
        # Try to get the server health
        url = f"{SUPABASE_URL}/rest/v1/"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            print("✅ Supabase connection successful!")
            return True
        else:
            print(f"❌ Supabase connection failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

def create_test_session():
    """Create a test session using the RPC API"""
    try:
        session_id = str(uuid.uuid4())

        # Call the create_ai_agent_session function
        url = f"{SUPABASE_URL}/rest/v1/rpc/create_ai_agent_session"
        data = {
            "p_id": session_id,
            "p_system_prompt": "Test system prompt",
            "p_title": "Test Session",
            "p_tags": "test,integration",
            "p_is_multi_agent": False
        }
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            print(f"✅ Test session created with ID: {session_id}")
            return session_id
        else:
            print(f"❌ Error creating test session: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating test session: {str(e)}")
        return None

def get_session(session_id):
    """Get a session using the RPC API"""
    try:
        # Call the get_ai_agent_session function
        url = f"{SUPABASE_URL}/rest/v1/rpc/get_ai_agent_session"
        response = requests.post(url, headers=headers, json={"p_id": session_id})

        if response.status_code == 200 and response.json():
            session = response.json()
            print(f"✅ Session retrieved: {json.dumps(session, indent=2)}")
            return session
        else:
            print(f"❌ Session not found: {session_id} - {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting session: {str(e)}")
        return None

def main():
    """Main function"""
    print("Testing Supabase connection...")
    connection_successful = test_connection()

    if connection_successful:
        print("\nCreating test session...")
        session_id = create_test_session()

        if session_id:
            print("\nRetrieving test session...")
            get_session(session_id)

    print("\nDone!")

if __name__ == "__main__":
    main()
