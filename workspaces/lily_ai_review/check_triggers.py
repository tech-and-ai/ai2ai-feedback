#!/usr/bin/env python3
"""
Script to check for triggers and rules on auth.users table.
"""

from app.utils.supabase_client import get_supabase_client

def main():
    """Main function to check for triggers and rules."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Check for triggers on auth.users
    triggers_query = """
    SELECT 
        trigger_name,
        event_manipulation,
        action_statement
    FROM 
        information_schema.triggers
    WHERE 
        event_object_schema = 'auth'
        AND event_object_table = 'users'
    """
    
    triggers_response = supabase.rpc('execute_sql', {'query': triggers_query}).execute()
    
    print('Triggers on auth.users:')
    if triggers_response.data:
        for trigger in triggers_response.data:
            print(f"- {trigger['trigger_name']} ({trigger['event_manipulation']})")
            print(f"  Action: {trigger['action_statement']}")
    else:
        print("No triggers found on auth.users table.")
    
    # Check for rules on auth.users
    rules_query = """
    SELECT 
        r.rulename,
        r.ev_type,
        r.ev_enabled,
        r.is_instead,
        pg_get_ruledef(r.oid) as rule_definition
    FROM 
        pg_rewrite r
    JOIN 
        pg_class c ON r.ev_class = c.oid
    JOIN 
        pg_namespace n ON c.relnamespace = n.oid
    WHERE 
        n.nspname = 'auth'
        AND c.relname = 'users'
        AND r.rulename != '_RETURN'
    """
    
    rules_response = supabase.rpc('execute_sql', {'query': rules_query}).execute()
    
    print('\nRules on auth.users:')
    if rules_response.data:
        for rule in rules_response.data:
            print(f"- {rule['rulename']} ({rule['ev_type']})")
            print(f"  Enabled: {rule['ev_enabled']}")
            print(f"  Instead: {rule['is_instead']}")
            print(f"  Definition: {rule['rule_definition']}")
    else:
        print("No rules found on auth.users table.")
    
    # Check for RLS policies on auth.users
    rls_query = """
    SELECT 
        p.policyname,
        p.cmd,
        p.permissive,
        pg_get_expr(p.qual, p.tableid) as expression,
        pg_get_expr(p.with_check, p.tableid) as with_check
    FROM 
        pg_policy p
    JOIN 
        pg_class c ON p.tableid = c.oid
    JOIN 
        pg_namespace n ON c.relnamespace = n.oid
    WHERE 
        n.nspname = 'auth'
        AND c.relname = 'users'
    """
    
    rls_response = supabase.rpc('execute_sql', {'query': rls_query}).execute()
    
    print('\nRLS policies on auth.users:')
    if rls_response.data:
        for policy in rls_response.data:
            print(f"- {policy['policyname']} ({policy['cmd']})")
            print(f"  Permissive: {policy['permissive']}")
            print(f"  Expression: {policy['expression']}")
            print(f"  With Check: {policy['with_check']}")
    else:
        print("No RLS policies found on auth.users table.")

if __name__ == '__main__':
    main()
