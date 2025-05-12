#!/usr/bin/env python3
"""
Script to fix user deletion issues in Supabase by adding ON DELETE CASCADE to all foreign key constraints.
"""

import os
import logging
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_user_deletion():
    """Fix user deletion issues by adding ON DELETE CASCADE to all foreign key constraints."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # Step 1: Find all tables with foreign keys to auth.users
    logger.info("Finding all tables with foreign keys to auth.users...")
    
    fk_query = """
    SELECT 
        tc.table_schema,
        tc.table_name,
        tc.constraint_name, 
        kcu.column_name, 
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        rc.delete_rule
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
    JOIN
        information_schema.referential_constraints AS rc
        ON rc.constraint_name = tc.constraint_name
        AND rc.constraint_schema = tc.table_schema
    WHERE 
        tc.constraint_type = 'FOREIGN KEY' 
        AND (
            (ccu.table_schema = 'auth' AND ccu.table_name = 'users')
            OR kcu.column_name = 'user_id'
        )
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': fk_query}).execute()
        
        if not response.data:
            logger.info("No foreign key constraints to auth.users found.")
            
            # Step 2: Find all tables with user_id column that might need constraints
            logger.info("Finding all tables with user_id column...")
            
            tables_query = """
            SELECT 
                table_schema, 
                table_name,
                column_name
            FROM 
                information_schema.columns
            WHERE 
                column_name = 'user_id'
                AND table_schema NOT IN ('pg_catalog', 'information_schema')
            """
            
            tables_response = supabase.rpc('execute_sql', {'query': tables_query}).execute()
            
            if tables_response.data:
                logger.info(f"Found {len(tables_response.data)} tables with user_id column.")
                
                for table in tables_response.data:
                    if isinstance(table, dict):
                        schema = table.get('table_schema')
                        table_name = table.get('table_name')
                        column = table.get('column_name')
                    else:
                        # Try to parse the table info
                        parts = str(table).split('.')
                        if len(parts) >= 2:
                            schema = parts[0]
                            table_name = parts[1]
                            column = 'user_id'
                        else:
                            logger.warning(f"Could not parse table info: {table}")
                            continue
                    
                    # Add ON DELETE CASCADE constraint
                    constraint_name = f"{table_name}_{column}_fkey"
                    
                    add_constraint_query = f"""
                    ALTER TABLE {schema}.{table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    FOREIGN KEY ({column}) 
                    REFERENCES auth.users(id) 
                    ON DELETE CASCADE;
                    """
                    
                    try:
                        logger.info(f"Adding ON DELETE CASCADE constraint to {schema}.{table_name}.{column}...")
                        constraint_response = supabase.rpc('execute_sql', {'query': add_constraint_query}).execute()
                        logger.info(f"Successfully added constraint to {schema}.{table_name}")
                    except Exception as e:
                        logger.error(f"Error adding constraint to {schema}.{table_name}: {str(e)}")
            else:
                logger.info("No tables with user_id column found.")
        else:
            logger.info(f"Found {len(response.data)} foreign key constraints to auth.users.")
            
            # Step 3: Update existing foreign key constraints to add ON DELETE CASCADE
            for constraint in response.data:
                if isinstance(constraint, dict):
                    schema = constraint.get('table_schema')
                    table_name = constraint.get('table_name')
                    constraint_name = constraint.get('constraint_name')
                    column = constraint.get('column_name')
                    delete_rule = constraint.get('delete_rule')
                else:
                    logger.warning(f"Could not parse constraint info: {constraint}")
                    continue
                
                if delete_rule == 'CASCADE':
                    logger.info(f"Constraint {constraint_name} already has ON DELETE CASCADE.")
                    continue
                
                logger.info(f"Updating constraint {constraint_name} on {schema}.{table_name}.{column} to add ON DELETE CASCADE...")
                
                # Drop the existing constraint
                drop_query = f"""
                ALTER TABLE {schema}.{table_name} 
                DROP CONSTRAINT IF EXISTS {constraint_name};
                """
                
                # Add a new constraint with ON DELETE CASCADE
                add_query = f"""
                ALTER TABLE {schema}.{table_name} 
                ADD CONSTRAINT {constraint_name} 
                FOREIGN KEY ({column}) 
                REFERENCES auth.users(id) 
                ON DELETE CASCADE;
                """
                
                try:
                    # Drop the existing constraint
                    drop_response = supabase.rpc('execute_sql', {'query': drop_query}).execute()
                    logger.info(f"Successfully dropped constraint {constraint_name}")
                    
                    # Add the new constraint with ON DELETE CASCADE
                    add_response = supabase.rpc('execute_sql', {'query': add_query}).execute()
                    logger.info(f"Successfully added ON DELETE CASCADE to constraint {constraint_name}")
                except Exception as e:
                    logger.error(f"Error updating constraint {constraint_name}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error finding foreign key constraints: {str(e)}")
    
    # Step 4: Check for any triggers that might interfere with deletion
    logger.info("Checking for triggers that might interfere with deletion...")
    
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
        t.action_statement LIKE '%auth.users%'
        OR t.action_statement LIKE '%user_id%'
    """
    
    try:
        triggers_response = supabase.rpc('execute_sql', {'query': triggers_query}).execute()
        
        if triggers_response.data:
            logger.info(f"Found {len(triggers_response.data)} triggers that might interfere with deletion.")
            
            for trigger in triggers_response.data:
                if isinstance(trigger, dict):
                    trigger_name = trigger.get('trigger_name')
                    schema = trigger.get('event_object_schema')
                    table = trigger.get('event_object_table')
                    event = trigger.get('event_manipulation')
                    
                    logger.info(f"Found trigger {trigger_name} on {schema}.{table} for {event} events.")
                    logger.info(f"You may need to manually review this trigger if deletion issues persist.")
        else:
            logger.info("No triggers found that might interfere with deletion.")
    except Exception as e:
        logger.error(f"Error checking triggers: {str(e)}")
    
    logger.info("User deletion fix completed. Try deleting a user from the Supabase dashboard now.")

if __name__ == '__main__':
    fix_user_deletion()
