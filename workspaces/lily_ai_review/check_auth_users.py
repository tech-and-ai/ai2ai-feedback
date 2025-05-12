#!/usr/bin/env python3
"""
Script to check the auth.users table structure.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check the auth.users table structure."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check auth.users table structure
    table_query = """
    SELECT 
        column_name, 
        data_type, 
        is_nullable, 
        column_default
    FROM 
        information_schema.columns
    WHERE 
        table_schema = 'auth' 
        AND table_name = 'users'
    ORDER BY 
        ordinal_position
    """
    
    table_response = supabase.rpc('execute_sql', {'query': table_query}).execute()
    
    print('auth.users table structure:')
    if table_response.data:
        for column in table_response.data:
            if isinstance(column, dict):
                print(f"- {column.get('column_name')} ({column.get('data_type')})")
                print(f"  Nullable: {column.get('is_nullable')}")
                print(f"  Default: {column.get('column_default')}")
            else:
                print(f"- {column}")
    else:
        print("Could not retrieve auth.users table structure.")
    
    # Check for constraints on auth.users
    constraints_query = """
    SELECT 
        tc.constraint_name, 
        tc.constraint_type, 
        kcu.column_name
    FROM 
        information_schema.table_constraints tc
    JOIN 
        information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
    WHERE 
        tc.table_schema = 'auth' 
        AND tc.table_name = 'users'
    """
    
    constraints_response = supabase.rpc('execute_sql', {'query': constraints_query}).execute()
    
    print('\nConstraints on auth.users:')
    if constraints_response.data:
        for constraint in constraints_response.data:
            if isinstance(constraint, dict):
                print(f"- {constraint.get('constraint_name')} ({constraint.get('constraint_type')})")
                print(f"  Column: {constraint.get('column_name')}")
            else:
                print(f"- {constraint}")
    else:
        print("Could not retrieve constraints on auth.users table.")
    
    # Check for references to auth.users
    references_query = """
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
    
    references_response = supabase.rpc('execute_sql', {'query': references_query}).execute()
    
    print('\nReferences to auth.users:')
    if references_response.data:
        for reference in references_response.data:
            if isinstance(reference, dict):
                print(f"- {reference.get('table_schema')}.{reference.get('table_name')}.{reference.get('column_name')}")
                print(f"  References: {reference.get('foreign_table_schema')}.{reference.get('foreign_table_name')}.{reference.get('foreign_column_name')}")
            else:
                print(f"- {reference}")
    else:
        print("No references to auth.users found in the information_schema.")

if __name__ == '__main__':
    main()
