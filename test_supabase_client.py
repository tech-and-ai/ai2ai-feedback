"""
Test the connection to the Supabase database using the Supabase client library.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

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

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    """Test the connection to the Supabase database"""
    try:
        # Try to get the server version
        response = supabase.rpc('execute_sql', {'query': 'SELECT version()'}).execute()

        if response.data:
            print("✅ Successfully connected to Supabase")
            print(f"Server version: {response.data}")
            return True
        else:
            print(f"❌ Error connecting to Supabase: {response.error}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False

def check_ai_agent_system_schema():
    """Check if the ai_agent_system schema exists"""
    try:
        response = supabase.rpc('execute_sql', {
            'query': """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = 'ai_agent_system'
            """
        }).execute()

        if response.data and len(response.data) > 0:
            print("✅ Schema 'ai_agent_system' exists")
            return True
        else:
            print("❓ Schema 'ai_agent_system' does not exist")
            return False
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
        return False

def check_tables():
    """Check if the required tables exist in the schema"""
    tables = [
        "sessions", "messages", "feedback", "agents",
        "tasks", "task_contexts", "task_updates"
    ]

    try:
        for table in tables:
            response = supabase.rpc('execute_sql', {
                'query': f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'ai_agent_system'
                AND table_name = '{table}'
                """
            }).execute()

            if response.data and len(response.data) > 0:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❓ Table '{table}' does not exist")
    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")

def create_schema():
    """Create the ai_agent_system schema if it doesn't exist"""
    try:
        response = supabase.rpc('execute_sql', {
            'query': "CREATE SCHEMA IF NOT EXISTS ai_agent_system"
        }).execute()

        if response.error:
            print(f"❌ Error creating schema: {response.error}")
            return False

        print("✅ Schema 'ai_agent_system' created or already exists")
        return True
    except Exception as e:
        print(f"❌ Error creating schema: {str(e)}")
        return False

def main():
    """Main function"""
    print("Testing connection to Supabase...")
    if test_connection():
        schema_exists = check_ai_agent_system_schema()

        if not schema_exists:
            create_schema()

        check_tables()

    print("\nDone!")

if __name__ == "__main__":
    main()
