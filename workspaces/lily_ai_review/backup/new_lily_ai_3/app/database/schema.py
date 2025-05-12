"""
Database schema for Lily AI.

This module provides functions to create and manage the database schema.
"""

import logging
from typing import List, Dict, Any, Optional
from app.database import get_db_client

# Set up logging
logger = logging.getLogger(__name__)

def create_schema() -> bool:
    """
    Create the database schema for Lily AI.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        db_client = get_db_client()
        
        # Create subscriptions table
        subscriptions_query = """
        CREATE TABLE IF NOT EXISTS public.lily_subscriptions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free',
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            stripe_subscription_id VARCHAR(255),
            stripe_customer_id VARCHAR(255),
            papers_limit INTEGER NOT NULL DEFAULT 0,
            papers_used INTEGER NOT NULL DEFAULT 0,
            start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            end_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_lily_subscriptions_user_id ON public.lily_subscriptions (user_id);
        CREATE INDEX IF NOT EXISTS idx_lily_subscriptions_stripe_subscription_id ON public.lily_subscriptions (stripe_subscription_id);
        CREATE INDEX IF NOT EXISTS idx_lily_subscriptions_stripe_customer_id ON public.lily_subscriptions (stripe_customer_id);
        """
        
        db_client.execute_query(subscriptions_query)
        logger.info("Created lily_subscriptions table")
        
        # Create payments table
        payments_query = """
        CREATE TABLE IF NOT EXISTS public.lily_payments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            subscription_id UUID REFERENCES public.lily_subscriptions(id) ON DELETE SET NULL,
            stripe_payment_intent_id VARCHAR(255),
            stripe_invoice_id VARCHAR(255),
            amount INTEGER NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'usd',
            status VARCHAR(50) NOT NULL,
            payment_method VARCHAR(50),
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_lily_payments_user_id ON public.lily_payments (user_id);
        CREATE INDEX IF NOT EXISTS idx_lily_payments_subscription_id ON public.lily_payments (subscription_id);
        CREATE INDEX IF NOT EXISTS idx_lily_payments_stripe_payment_intent_id ON public.lily_payments (stripe_payment_intent_id);
        """
        
        db_client.execute_query(payments_query)
        logger.info("Created lily_payments table")
        
        # Create papers table
        papers_query = """
        CREATE TABLE IF NOT EXISTS public.lily_papers (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            topic VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_lily_papers_user_id ON public.lily_papers (user_id);
        CREATE INDEX IF NOT EXISTS idx_lily_papers_topic ON public.lily_papers (topic);
        """
        
        db_client.execute_query(papers_query)
        logger.info("Created lily_papers table")
        
        # Create settings table
        settings_query = """
        CREATE TABLE IF NOT EXISTS public.lily_settings (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            settings JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT unique_lily_settings_user_id UNIQUE (user_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_lily_settings_user_id ON public.lily_settings (user_id);
        """
        
        db_client.execute_query(settings_query)
        logger.info("Created lily_settings table")
        
        return True
    except Exception as e:
        logger.error(f"Error creating schema: {str(e)}")
        return False

def check_schema() -> Dict[str, bool]:
    """
    Check if the database schema exists.
    
    Returns:
        A dictionary with table names as keys and existence status as values
    """
    try:
        db_client = get_db_client()
        tables = ["lily_subscriptions", "lily_payments", "lily_papers", "lily_settings"]
        result = {}
        
        for table_name in tables:
            query = f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table_name}'
            );
            """
            
            response = db_client.execute_query(query)
            exists = response[0].get('exists', False) if response else False
            result[table_name] = exists
        
        return result
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")
        return {table_name: False for table_name in ["lily_subscriptions", "lily_payments", "lily_papers", "lily_settings"]}
