import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.environ.get("SUPABASE_PROJECT_URL")
supabase_key = os.environ.get("SUPABASE_API_KEY")

# Initialize Supabase client
supabase = create_client(supabase_url, supabase_key)

# List tables
try:
    # Query to list all tables in the public schema
    response = supabase.rpc('list_tables').execute()
    print("Tables in the database:")
    for table in response.data:
        print(f"- {table}")
except Exception as e:
    print(f"Error listing tables: {str(e)}")
    
    # Try alternative approach
    try:
        # Query information_schema.tables
        response = supabase.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
        print("\nTables in the public schema:")
        for table in response.data:
            print(f"- {table['table_name']}")
    except Exception as e2:
        print(f"Error with alternative approach: {str(e2)}")
