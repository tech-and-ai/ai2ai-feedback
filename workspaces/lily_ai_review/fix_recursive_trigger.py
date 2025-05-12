#!/usr/bin/env python3
"""
Script to fix recursive trigger issues in the database.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Fix recursive trigger issues in the database."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check for triggers on saas_user_subscriptions
    print("Checking for triggers on saas_user_subscriptions...")
    triggers_query = """
    SELECT 
        trigger_name,
        event_manipulation,
        action_statement
    FROM 
        information_schema.triggers
    WHERE 
        event_object_schema = 'public'
        AND event_object_table = 'saas_user_subscriptions'
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': triggers_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} triggers on saas_user_subscriptions:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('trigger_name')} ({item.get('event_manipulation')})")
                    print(f"  Action: {item.get('action_statement')}")
                else:
                    print(f"- {item}")
        else:
            print("No triggers found on saas_user_subscriptions table.")
    except Exception as e:
        print(f"Error checking triggers: {str(e)}")
    
    # Check for triggers on saas_users
    print("\nChecking for triggers on saas_users...")
    triggers_query = """
    SELECT 
        trigger_name,
        event_manipulation,
        action_statement
    FROM 
        information_schema.triggers
    WHERE 
        event_object_schema = 'public'
        AND event_object_table = 'saas_users'
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': triggers_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} triggers on saas_users:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('trigger_name')} ({item.get('event_manipulation')})")
                    print(f"  Action: {item.get('action_statement')}")
                else:
                    print(f"- {item}")
        else:
            print("No triggers found on saas_users table.")
    except Exception as e:
        print(f"Error checking triggers: {str(e)}")
    
    # Check for foreign key constraints on saas_user_subscriptions
    print("\nChecking for foreign key constraints on saas_user_subscriptions...")
    fk_query = """
    SELECT 
        tc.constraint_name, 
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
        AND tc.table_schema = 'public'
        AND tc.table_name = 'saas_user_subscriptions'
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': fk_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} foreign key constraints on saas_user_subscriptions:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('constraint_name')}: {item.get('column_name')} -> {item.get('foreign_table_schema')}.{item.get('foreign_table_name')}.{item.get('foreign_column_name')}")
                else:
                    print(f"- {item}")
        else:
            print("No foreign key constraints found on saas_user_subscriptions table.")
    except Exception as e:
        print(f"Error checking foreign key constraints: {str(e)}")
    
    # Try to fix the issue by dropping and recreating the foreign key constraint
    print("\nAttempting to fix the issue by dropping and recreating foreign key constraints...")
    
    # First, identify the constraint name
    constraint_name = None
    try:
        response = supabase.rpc('execute_sql', {'query': fk_query}).execute()
        if response.data and len(response.data) > 0:
            for item in response.data:
                if isinstance(item, dict) and item.get('foreign_table_schema') == 'auth' and item.get('foreign_table_name') == 'users':
                    constraint_name = item.get('constraint_name')
                    break
    except Exception as e:
        print(f"Error identifying constraint: {str(e)}")
    
    if constraint_name:
        print(f"Found constraint to drop: {constraint_name}")
        
        # Drop the constraint
        drop_query = f"""
        ALTER TABLE public.saas_user_subscriptions DROP CONSTRAINT IF EXISTS {constraint_name};
        """
        
        try:
            response = supabase.rpc('execute_sql', {'query': drop_query}).execute()
            print("Successfully dropped the constraint.")
        except Exception as e:
            print(f"Error dropping constraint: {str(e)}")
    else:
        print("No auth.users foreign key constraint found on saas_user_subscriptions.")
        
        # Try to create a new constraint with ON DELETE CASCADE
        print("\nAttempting to add ON DELETE CASCADE to user_id foreign key...")
        
        add_constraint_query = """
        ALTER TABLE public.saas_user_subscriptions 
        ADD CONSTRAINT saas_user_subscriptions_user_id_fkey 
        FOREIGN KEY (user_id) 
        REFERENCES auth.users(id) 
        ON DELETE CASCADE;
        """
        
        try:
            response = supabase.rpc('execute_sql', {'query': add_constraint_query}).execute()
            print("Successfully added ON DELETE CASCADE constraint.")
        except Exception as e:
            print(f"Error adding constraint: {str(e)}")
    
    # Check for any other tables with foreign keys to auth.users
    print("\nChecking for other tables with foreign keys to auth.users...")
    other_fk_query = """
    SELECT 
        tc.table_schema,
        tc.table_name,
        tc.constraint_name, 
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
    
    try:
        response = supabase.rpc('execute_sql', {'query': other_fk_query}).execute()
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} other tables with foreign keys to auth.users:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('table_schema')}.{item.get('table_name')}.{item.get('column_name')} -> auth.users.{item.get('foreign_column_name')}")
                    
                    # Try to update this constraint to add ON DELETE CASCADE
                    table_schema = item.get('table_schema')
                    table_name = item.get('table_name')
                    constraint_name = item.get('constraint_name')
                    column_name = item.get('column_name')
                    
                    if table_schema and table_name and constraint_name and column_name:
                        print(f"  Attempting to update constraint {constraint_name} to add ON DELETE CASCADE...")
                        
                        # Drop the existing constraint
                        drop_query = f"""
                        ALTER TABLE {table_schema}.{table_name} DROP CONSTRAINT IF EXISTS {constraint_name};
                        """
                        
                        try:
                            response = supabase.rpc('execute_sql', {'query': drop_query}).execute()
                            print(f"  Successfully dropped constraint {constraint_name}.")
                            
                            # Add a new constraint with ON DELETE CASCADE
                            add_query = f"""
                            ALTER TABLE {table_schema}.{table_name} 
                            ADD CONSTRAINT {constraint_name} 
                            FOREIGN KEY ({column_name}) 
                            REFERENCES auth.users(id) 
                            ON DELETE CASCADE;
                            """
                            
                            try:
                                response = supabase.rpc('execute_sql', {'query': add_query}).execute()
                                print(f"  Successfully added ON DELETE CASCADE to constraint {constraint_name}.")
                            except Exception as e:
                                print(f"  Error adding constraint: {str(e)}")
                        except Exception as e:
                            print(f"  Error dropping constraint: {str(e)}")
                else:
                    print(f"- {item}")
        else:
            print("No other tables with foreign keys to auth.users found.")
    except Exception as e:
        print(f"Error checking other foreign key constraints: {str(e)}")

if __name__ == '__main__':
    main()
