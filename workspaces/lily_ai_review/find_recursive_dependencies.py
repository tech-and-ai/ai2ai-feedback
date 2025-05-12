#!/usr/bin/env python3
"""
Script to find recursive dependencies in the database.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Find recursive dependencies in the database."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check for recursive triggers
    print("Checking for recursive triggers...")
    recursive_triggers_query = """
    WITH RECURSIVE trigger_chain AS (
        SELECT 
            t.trigger_name,
            t.event_object_schema,
            t.event_object_table,
            t.action_statement,
            ARRAY[t.trigger_name] AS trigger_path
        FROM 
            information_schema.triggers t
        
        UNION ALL
        
        SELECT 
            t.trigger_name,
            t.event_object_schema,
            t.event_object_table,
            t.action_statement,
            tc.trigger_path || t.trigger_name
        FROM 
            information_schema.triggers t,
            trigger_chain tc
        WHERE 
            t.action_statement LIKE '%' || tc.trigger_name || '%'
            AND t.trigger_name <> ALL(tc.trigger_path)
    )
    SELECT 
        trigger_path
    FROM 
        trigger_chain
    WHERE 
        array_length(trigger_path, 1) > 1;
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': recursive_triggers_query}).execute()
        if response.data and len(response.data) > 0:
            print("Found recursive triggers:")
            for item in response.data:
                print(f"- {item}")
        else:
            print("No recursive triggers found.")
    except Exception as e:
        print(f"Error checking recursive triggers: {str(e)}")
    
    # Check for circular foreign key references
    print("\nChecking for circular foreign key references...")
    circular_fk_query = """
    WITH RECURSIVE fk_chain AS (
        SELECT 
            tc.table_schema AS source_schema,
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_schema AS target_schema,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column,
            ARRAY[tc.table_schema || '.' || tc.table_name] AS table_path
        FROM 
            information_schema.table_constraints tc
        JOIN 
            information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN 
            information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE 
            tc.constraint_type = 'FOREIGN KEY'
        
        UNION ALL
        
        SELECT 
            tc.table_schema AS source_schema,
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_schema AS target_schema,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column,
            fk.table_path || (tc.table_schema || '.' || tc.table_name)
        FROM 
            information_schema.table_constraints tc
        JOIN 
            information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN 
            information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN 
            fk_chain fk 
            ON fk.target_schema = tc.table_schema
            AND fk.target_table = tc.table_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY'
            AND (tc.table_schema || '.' || tc.table_name) <> ALL(fk.table_path)
    )
    SELECT 
        table_path || (target_schema || '.' || target_table) AS circular_reference
    FROM 
        fk_chain
    WHERE 
        (target_schema || '.' || target_table) = ANY(table_path);
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': circular_fk_query}).execute()
        if response.data and len(response.data) > 0:
            print("Found circular foreign key references:")
            for item in response.data:
                print(f"- {item}")
        else:
            print("No circular foreign key references found.")
    except Exception as e:
        print(f"Error checking circular foreign keys: {str(e)}")
    
    # Check for tables with user_id columns that might have data for auth.users
    print("\nChecking for tables with user_id columns that might have data for auth users...")
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
    
    try:
        tables_response = supabase.rpc('execute_sql', {'query': tables_query}).execute()
        
        for table_info in tables_response.data:
            if isinstance(table_info, str):
                # Parse the table info string
                parts = table_info.split('.')
                if len(parts) == 2:
                    schema, table = parts
                else:
                    schema = 'public'
                    table = table_info
            else:
                # Extract schema and table from dictionary
                schema = table_info.get('table_schema', 'unknown')
                table = table_info.get('table_name', 'unknown')
            
            # Skip system tables
            if schema in ['pg_catalog', 'information_schema']:
                continue
                
            # Check if this table has a user_id column
            columns_query = f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema}' 
            AND table_name = '{table}' 
            AND column_name IN ('user_id', 'id')
            """
            
            try:
                columns_response = supabase.rpc('execute_sql', {'query': columns_query}).execute()
                
                if columns_response.data:
                    for column_info in columns_response.data:
                        if isinstance(column_info, str):
                            column = column_info
                        else:
                            column = column_info.get('column_name', 'unknown')
                        
                        # Check if there are rows with this user ID
                        if column == 'user_id':
                            count_query = f"""
                            SELECT COUNT(*) FROM {schema}.{table} WHERE user_id IS NOT NULL
                            """
                            try:
                                count_response = supabase.rpc('execute_sql', {'query': count_query}).execute()
                                count = 0
                                
                                if count_response.data:
                                    count_info = count_response.data[0]
                                    if isinstance(count_info, dict):
                                        count = count_info.get('count', 0)
                                    elif isinstance(count_info, int):
                                        count = count_info
                                    else:
                                        try:
                                            count = int(count_info)
                                        except:
                                            count = 0
                                
                                if count > 0:
                                    print(f"- {schema}.{table}.{column} has {count} rows with user_id values")
                            except Exception as e:
                                print(f"  * Error checking count for {schema}.{table}.{column}: {str(e)}")
            except Exception as e:
                print(f"Error checking columns for {schema}.{table}: {str(e)}")
    except Exception as e:
        print(f"Error checking tables: {str(e)}")

if __name__ == '__main__':
    main()
