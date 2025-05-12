#!/usr/bin/env python3
"""
Script to check foreign key constraints to auth.users table.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check foreign key constraints."""
    # Get Supabase client
    supabase = get_supabase_client()

    # Query to find foreign key constraints to auth.users
    query = """
    SELECT
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM
        information_schema.table_constraints AS tc
    JOIN
        information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN
        information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE
        tc.constraint_type = 'FOREIGN KEY'
        AND ccu.table_schema = 'auth'
        AND ccu.table_name = 'users'
    """

    response = supabase.rpc('execute_sql', {'query': query}).execute()

    print('Foreign key constraints to auth.users:')
    if response.data:
        for constraint in response.data:
            print(f"- {constraint['table_schema']}.{constraint['table_name']}.{constraint['column_name']} -> auth.users.{constraint['foreign_column_name']}")
    else:
        print("No foreign key constraints found in the information_schema.")

    # Check for tables that might have user_id columns
    tables_query = """
    SELECT
        table_schema,
        table_name
    FROM
        information_schema.tables
    WHERE
        table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
    """

    tables_response = supabase.rpc('execute_sql', {'query': tables_query}).execute()

    print('\nChecking tables for user_id columns:')
    for table in tables_response.data:
        if isinstance(table, dict):
            schema = table.get('table_schema')
            table_name = table.get('table_name')
        else:
            # If the response is not a dictionary, try to parse it
            try:
                parts = table.split('.')
                if len(parts) == 2:
                    schema, table_name = parts
                else:
                    schema = 'public'
                    table_name = table
            except:
                print(f"Could not parse table: {table}")
                continue

        # Skip auth.users table itself
        if schema == 'auth' and table_name == 'users':
            continue

        columns_query = f"""
        SELECT
            column_name
        FROM
            information_schema.columns
        WHERE
            table_schema = '{schema}'
            AND table_name = '{table_name}'
            AND column_name IN ('user_id', 'id')
        """

        columns_response = supabase.rpc('execute_sql', {'query': columns_query}).execute()

        if columns_response.data:
            for column in columns_response.data:
                print(f"- {schema}.{table_name}.{column['column_name']}")

                # Check if there are rows with this user ID
                if column['column_name'] == 'user_id':
                    count_query = f"""
                    SELECT COUNT(*) FROM {schema}.{table_name} WHERE user_id IS NOT NULL
                    """
                    try:
                        count_response = supabase.rpc('execute_sql', {'query': count_query}).execute()
                        if count_response.data and count_response.data[0]['count'] > 0:
                            print(f"  * Has {count_response.data[0]['count']} rows with user_id values")
                    except Exception as e:
                        print(f"  * Error checking count: {str(e)}")

if __name__ == '__main__':
    main()
