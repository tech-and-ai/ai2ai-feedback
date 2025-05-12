#!/usr/bin/env python3
"""
Script to check for auth-related functions and triggers.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Check for auth-related functions and triggers."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check for auth-related functions
    print("Checking for auth-related functions...")
    functions_query = """
    SELECT 
        n.nspname AS schema_name,
        p.proname AS function_name,
        pg_get_functiondef(p.oid) AS function_definition
    FROM 
        pg_proc p
    JOIN 
        pg_namespace n ON p.pronamespace = n.oid
    WHERE 
        n.nspname = 'auth'
        OR p.proname LIKE '%auth%'
        OR p.proname LIKE '%user%'
    ORDER BY 
        n.nspname, p.proname;
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': functions_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} auth-related functions:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('schema_name')}.{item.get('function_name')}")
                else:
                    print(f"- {item}")
        else:
            print("No auth-related functions found.")
    except Exception as e:
        print(f"Error checking auth-related functions: {str(e)}")
    
    # Check for auth-related triggers
    print("\nChecking for auth-related triggers...")
    triggers_query = """
    SELECT 
        t.trigger_name,
        t.event_object_schema,
        t.event_object_table,
        t.event_manipulation,
        t.action_statement
    FROM 
        information_schema.triggers t
    WHERE 
        t.event_object_schema = 'auth'
        OR t.trigger_name LIKE '%auth%'
        OR t.trigger_name LIKE '%user%'
    ORDER BY 
        t.event_object_schema, t.event_object_table, t.trigger_name;
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': triggers_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} auth-related triggers:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('trigger_name')} on {item.get('event_object_schema')}.{item.get('event_object_table')} ({item.get('event_manipulation')})")
                else:
                    print(f"- {item}")
        else:
            print("No auth-related triggers found.")
    except Exception as e:
        print(f"Error checking auth-related triggers: {str(e)}")
    
    # Check for tables with references to auth.users
    print("\nChecking for tables with references to auth.users...")
    references_query = """
    SELECT 
        c.relname AS table_name,
        n.nspname AS schema_name,
        a.attname AS column_name,
        pg_get_expr(d.adbin, d.adrelid) AS default_expr
    FROM 
        pg_class c
    JOIN 
        pg_namespace n ON c.relnamespace = n.oid
    JOIN 
        pg_attribute a ON a.attrelid = c.oid
    LEFT JOIN 
        pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
    WHERE 
        c.relkind = 'r'
        AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        AND (
            pg_get_expr(d.adbin, d.adrelid) LIKE '%auth.users%'
            OR pg_get_expr(d.adbin, d.adrelid) LIKE '%auth%user%'
        )
    ORDER BY 
        n.nspname, c.relname, a.attname;
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': references_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} columns with references to auth.users:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('schema_name')}.{item.get('table_name')}.{item.get('column_name')}")
                    print(f"  Default: {item.get('default_expr')}")
                else:
                    print(f"- {item}")
        else:
            print("No columns with references to auth.users found.")
    except Exception as e:
        print(f"Error checking references to auth.users: {str(e)}")

if __name__ == '__main__':
    main()
