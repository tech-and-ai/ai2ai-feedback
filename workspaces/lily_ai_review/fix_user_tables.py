#!/usr/bin/env python3
"""
Script to fix user deletion issues by directly identifying and updating tables with user_id columns.
"""

import os
import logging
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_user_tables():
    """Fix user deletion issues by directly identifying and updating tables with user_id columns."""
    # Get Supabase client
    supabase = get_supabase_client()
    
    # List of tables we know have user_id columns
    known_tables = [
        {"schema": "public", "table": "saas_users", "column": "id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_user_subscriptions", "column": "user_id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_papers", "column": "user_id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_paper_credits", "column": "user_id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_paper_credit_usage", "column": "user_id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_notification_logs", "column": "user_id", "references": "auth.users(id)"},
        {"schema": "public", "table": "saas_job_tracking", "column": "user_id", "references": "auth.users(id)"}
    ]
    
    # Process each known table
    for table_info in known_tables:
        schema = table_info["schema"]
        table = table_info["table"]
        column = table_info["column"]
        references = table_info["references"]
        
        # Check if the table exists
        table_check_query = f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = '{schema}' 
            AND table_name = '{table}'
        );
        """
        
        try:
            response = supabase.rpc('execute_sql', {'query': table_check_query}).execute()
            table_exists = response.data[0].get('exists', False) if response.data else False
            
            if not table_exists:
                logger.info(f"Table {schema}.{table} does not exist, skipping.")
                continue
            
            logger.info(f"Processing table {schema}.{table}...")
            
            # Check if the column exists
            column_check_query = f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = '{schema}' 
                AND table_name = '{table}' 
                AND column_name = '{column}'
            );
            """
            
            response = supabase.rpc('execute_sql', {'query': column_check_query}).execute()
            column_exists = response.data[0].get('exists', False) if response.data else False
            
            if not column_exists:
                logger.info(f"Column {column} does not exist in {schema}.{table}, skipping.")
                continue
            
            # Check for existing foreign key constraints
            constraint_check_query = f"""
            SELECT 
                tc.constraint_name
            FROM 
                information_schema.table_constraints tc
            JOIN 
                information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE 
                tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = '{schema}' 
                AND tc.table_name = '{table}' 
                AND kcu.column_name = '{column}'
            """
            
            response = supabase.rpc('execute_sql', {'query': constraint_check_query}).execute()
            existing_constraints = [item.get('constraint_name') for item in response.data] if response.data else []
            
            # Drop existing constraints
            for constraint_name in existing_constraints:
                logger.info(f"Dropping existing constraint {constraint_name} on {schema}.{table}...")
                
                drop_query = f"""
                ALTER TABLE {schema}.{table} 
                DROP CONSTRAINT IF EXISTS {constraint_name};
                """
                
                try:
                    supabase.rpc('execute_sql', {'query': drop_query}).execute()
                    logger.info(f"Successfully dropped constraint {constraint_name}")
                except Exception as e:
                    logger.error(f"Error dropping constraint {constraint_name}: {str(e)}")
            
            # Add new constraint with ON DELETE CASCADE
            constraint_name = f"{table}_{column}_fkey"
            
            add_query = f"""
            ALTER TABLE {schema}.{table} 
            ADD CONSTRAINT {constraint_name} 
            FOREIGN KEY ({column}) 
            REFERENCES {references} 
            ON DELETE CASCADE;
            """
            
            try:
                logger.info(f"Adding ON DELETE CASCADE constraint to {schema}.{table}.{column}...")
                supabase.rpc('execute_sql', {'query': add_query}).execute()
                logger.info(f"Successfully added constraint to {schema}.{table}")
            except Exception as e:
                logger.error(f"Error adding constraint to {schema}.{table}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error processing table {schema}.{table}: {str(e)}")
    
    # Check for any other tables with user_id columns
    logger.info("Checking for any other tables with user_id columns...")
    
    tables_query = """
    SELECT 
        table_schema, 
        table_name
    FROM 
        information_schema.columns
    WHERE 
        column_name = 'user_id'
        AND table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_schema || '.' || table_name NOT IN (
            'public.saas_users', 'public.saas_user_subscriptions', 'public.saas_papers',
            'public.saas_paper_credits', 'public.saas_paper_credit_usage',
            'public.saas_notification_logs', 'public.saas_job_tracking'
        )
    GROUP BY 
        table_schema, table_name
    """
    
    try:
        response = supabase.rpc('execute_sql', {'query': tables_query}).execute()
        
        if response.data:
            logger.info(f"Found {len(response.data)} additional tables with user_id column.")
            
            for item in response.data:
                if isinstance(item, dict):
                    schema = item.get('table_schema')
                    table = item.get('table_name')
                else:
                    # Try to parse the item
                    parts = str(item).split('.')
                    if len(parts) == 2:
                        schema, table = parts
                    else:
                        logger.warning(f"Could not parse table info: {item}")
                        continue
                
                logger.info(f"Processing additional table {schema}.{table}...")
                
                # Check for existing foreign key constraints
                constraint_check_query = f"""
                SELECT 
                    tc.constraint_name
                FROM 
                    information_schema.table_constraints tc
                JOIN 
                    information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE 
                    tc.constraint_type = 'FOREIGN KEY' 
                    AND tc.table_schema = '{schema}' 
                    AND tc.table_name = '{table}' 
                    AND kcu.column_name = 'user_id'
                """
                
                response = supabase.rpc('execute_sql', {'query': constraint_check_query}).execute()
                existing_constraints = [item.get('constraint_name') for item in response.data] if response.data else []
                
                # Drop existing constraints
                for constraint_name in existing_constraints:
                    logger.info(f"Dropping existing constraint {constraint_name} on {schema}.{table}...")
                    
                    drop_query = f"""
                    ALTER TABLE {schema}.{table} 
                    DROP CONSTRAINT IF EXISTS {constraint_name};
                    """
                    
                    try:
                        supabase.rpc('execute_sql', {'query': drop_query}).execute()
                        logger.info(f"Successfully dropped constraint {constraint_name}")
                    except Exception as e:
                        logger.error(f"Error dropping constraint {constraint_name}: {str(e)}")
                
                # Add new constraint with ON DELETE CASCADE
                constraint_name = f"{table}_user_id_fkey"
                
                add_query = f"""
                ALTER TABLE {schema}.{table} 
                ADD CONSTRAINT {constraint_name} 
                FOREIGN KEY (user_id) 
                REFERENCES auth.users(id) 
                ON DELETE CASCADE;
                """
                
                try:
                    logger.info(f"Adding ON DELETE CASCADE constraint to {schema}.{table}.user_id...")
                    supabase.rpc('execute_sql', {'query': add_query}).execute()
                    logger.info(f"Successfully added constraint to {schema}.{table}")
                except Exception as e:
                    logger.error(f"Error adding constraint to {schema}.{table}: {str(e)}")
        else:
            logger.info("No additional tables with user_id column found.")
    
    except Exception as e:
        logger.error(f"Error checking for additional tables: {str(e)}")
    
    logger.info("User tables fix completed. Try deleting a user from the Supabase dashboard now.")

if __name__ == '__main__':
    fix_user_tables()
