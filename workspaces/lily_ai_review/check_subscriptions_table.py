#!/usr/bin/env python3
"""
Script to check the saas_user_subscriptions table structure.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Check the saas_user_subscriptions table structure."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check saas_user_subscriptions table structure
    print("Checking saas_user_subscriptions table structure...")
    table_query = """
    SELECT 
        column_name, 
        data_type, 
        is_nullable, 
        column_default
    FROM 
        information_schema.columns
    WHERE 
        table_schema = 'public' 
        AND table_name = 'saas_user_subscriptions'
    ORDER BY 
        ordinal_position
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': table_query}).execute()
        if response.data and len(response.data) > 0:
            print("saas_user_subscriptions table columns:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('column_name')} ({item.get('data_type')})")
                    print(f"  Nullable: {item.get('is_nullable')}")
                    print(f"  Default: {item.get('column_default')}")
                else:
                    print(f"- {item}")
        else:
            print("Could not retrieve saas_user_subscriptions table structure.")
    except Exception as e:
        print(f"Error checking saas_user_subscriptions table structure: {str(e)}")
    
    # Check for constraints on saas_user_subscriptions
    print("\nChecking constraints on saas_user_subscriptions...")
    constraints_query = """
    SELECT 
        tc.constraint_name, 
        tc.constraint_type, 
        kcu.column_name,
        ccu.table_schema AS referenced_table_schema,
        ccu.table_name AS referenced_table_name,
        ccu.column_name AS referenced_column_name
    FROM 
        information_schema.table_constraints tc
    JOIN 
        information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
    LEFT JOIN 
        information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
    WHERE 
        tc.table_schema = 'public' 
        AND tc.table_name = 'saas_user_subscriptions'
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': constraints_query}).execute()
        if response.data and len(response.data) > 0:
            print("saas_user_subscriptions constraints:")
            for item in response.data:
                if isinstance(item, dict):
                    constraint_type = item.get('constraint_type')
                    if constraint_type == 'FOREIGN KEY':
                        print(f"- {item.get('constraint_name')} ({constraint_type})")
                        print(f"  Column: {item.get('column_name')}")
                        print(f"  References: {item.get('referenced_table_schema')}.{item.get('referenced_table_name')}.{item.get('referenced_column_name')}")
                    else:
                        print(f"- {item.get('constraint_name')} ({constraint_type})")
                        print(f"  Column: {item.get('column_name')}")
                else:
                    print(f"- {item}")
        else:
            print("No constraints found on saas_user_subscriptions table.")
    except Exception as e:
        print(f"Error checking constraints on saas_user_subscriptions table: {str(e)}")
    
    # Check for triggers on saas_user_subscriptions
    print("\nChecking triggers on saas_user_subscriptions...")
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
            print("saas_user_subscriptions triggers:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- {item.get('trigger_name')} ({item.get('event_manipulation')})")
                    print(f"  Action: {item.get('action_statement')}")
                else:
                    print(f"- {item}")
        else:
            print("No triggers found on saas_user_subscriptions table.")
    except Exception as e:
        print(f"Error checking triggers on saas_user_subscriptions table: {str(e)}")
    
    # Check for data in saas_user_subscriptions
    print("\nChecking data in saas_user_subscriptions...")
    data_query = """
    SELECT 
        id, 
        user_id, 
        subscription_tier, 
        status, 
        stripe_subscription_id, 
        stripe_customer_id
    FROM 
        saas_user_subscriptions
    LIMIT 5
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': data_query}).execute()
        if response.data and len(response.data) > 0:
            print("Sample data from saas_user_subscriptions:")
            for item in response.data:
                if isinstance(item, dict):
                    print(f"- ID: {item.get('id')}")
                    print(f"  User ID: {item.get('user_id')}")
                    print(f"  Tier: {item.get('subscription_tier')}")
                    print(f"  Status: {item.get('status')}")
                    print(f"  Stripe Subscription ID: {item.get('stripe_subscription_id')}")
                    print(f"  Stripe Customer ID: {item.get('stripe_customer_id')}")
                else:
                    print(f"- {item}")
        else:
            print("No data found in saas_user_subscriptions table.")
    except Exception as e:
        print(f"Error checking data in saas_user_subscriptions table: {str(e)}")

if __name__ == '__main__':
    main()
