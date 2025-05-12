import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get('SUPABASE_PROJECT_URL')
key = os.environ.get('SUPABASE_API_KEY')
supabase = create_client(url, key)

# Query to find all foreign key constraints referencing auth.users
query = """
SELECT
    conrelid::regclass AS table_from,
    conname,
    pg_get_constraintdef(oid)
FROM
    pg_constraint
WHERE
    pg_get_constraintdef(oid) LIKE '%REFERENCES auth.users%'
    AND conrelid::regclass::text NOT LIKE 'auth.%'
"""

# Execute the query
result = supabase.rpc('execute_sql', {'query': query}).execute()

# Print the results
print("Foreign key constraints referencing auth.users:")
print(result.data)
if isinstance(result.data, list) and len(result.data) > 0:
    if isinstance(result.data[0], dict):
        for constraint in result.data:
            print(f"Table: {constraint['table_from']}, Constraint: {constraint['conname']}, Definition: {constraint['pg_get_constraintdef']}")
    else:
        print("Result data is not in the expected dictionary format")

# Query to drop all foreign key constraints referencing auth.users
drop_query = """
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Find all foreign key constraints referencing auth.users
    FOR r IN
        SELECT conrelid::regclass AS table_from, conname
        FROM pg_constraint
        WHERE pg_get_constraintdef(oid) LIKE '%REFERENCES auth.users%'
          AND conrelid::regclass::text NOT LIKE 'auth.%'
          AND conname NOT IN ('admin_users_id_fkey', 'saas_user_subscriptions_user_id_fkey')
    LOOP
        -- Drop each constraint
        EXECUTE 'ALTER TABLE ' || r.table_from || ' DROP CONSTRAINT ' || r.conname;
        RAISE NOTICE 'Dropped constraint % on table %', r.conname, r.table_from;
    END LOOP;
END
$$;
"""

# Automatically drop the constraints
print("\nDropping constraints...")
drop_result = supabase.rpc('execute_sql', {'query': drop_query}).execute()
print("Constraints dropped successfully!")
print(drop_result.data)
