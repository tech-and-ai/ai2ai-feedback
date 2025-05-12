"""
Test the connection to the Supabase database using the REST API.
"""

import os
import json
import requests
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
    """Test the connection to the Supabase database"""
    # Try to get the server version
    url = f"{SUPABASE_URL}/rest/v1/sessions?select=id&limit=1"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error connecting to Supabase: {response.status_code} - {response.text}")
        return False

    print("✅ Successfully connected to Supabase")
    return True

def check_ai_agent_system_tables():
    """Check if the ai_agent_system tables exist"""
    url = f"{SUPABASE_URL}/rest/v1/sessions?select=id&limit=1"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error checking tables: {response.status_code} - {response.text}")
        return False

    print("✅ Successfully queried the sessions table")
    return True

def main():
    """Main function"""
    print("Testing connection to Supabase...")
    if test_connection():
        check_ai_agent_system_tables()

    print("\nDone!")

if __name__ == "__main__":
    main()
