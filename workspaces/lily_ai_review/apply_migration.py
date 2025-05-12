#!/usr/bin/env python
"""
Apply a migration to the database.
"""
import sys
from app.services.supabase_service import get_supabase_client
from app.logging import get_logger

# Configure logging
logger = get_logger(__name__)

def main():
    """Execute the SQL migration script."""
    # Check if a migration file was specified
    if len(sys.argv) < 2:
        migration_file = 'migrations/add_user_notification_trigger.sql'
        print(f"No migration file specified, using default: {migration_file}")
    else:
        migration_file = sys.argv[1]

    print(f"Applying migration: {migration_file}")

    supabase = get_supabase_client()

    # Read the SQL file
    with open(migration_file, 'r') as f:
        sql = f.read()

    # Execute the SQL
    try:
        result = supabase.rpc('execute_sql', {'query': sql}).execute()
        print('Migration executed successfully')
    except Exception as e:
        print(f"Error executing migration: {str(e)}")

        # Try direct SQL execution if RPC fails
        try:
            print("Trying direct SQL execution...")
            migration_name = migration_file.split('/')[-1].replace('.sql', '')
            result = supabase.table('_migrations').insert({
                'name': migration_name,
                'sql': sql,
                'executed_at': 'now()'
            }).execute()
            print("Migration record created, now executing SQL directly...")

            # Split the SQL into individual statements
            statements = sql.split(';')
            for statement in statements:
                if statement.strip():
                    try:
                        result = supabase.sql(statement).execute()
                        print(f"Executed: {statement[:50]}...")
                    except Exception as inner_e:
                        print(f"Error executing statement: {str(inner_e)}")

            print("Direct SQL execution completed")
        except Exception as direct_e:
            print(f"Error with direct execution: {str(direct_e)}")

if __name__ == "__main__":
    main()
