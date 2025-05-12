#!/usr/bin/env python3
"""
Script to create a checkout URL for the premium subscription.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project directory to the path so we can import from it
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the Stripe service from the project
from app.services.billing.stripe_service import StripeService
from app.utils.supabase_client import get_supabase_client

def create_checkout_url():
    """
    Create a checkout URL for the premium subscription.
    """
    try:
        # Initialize the Stripe service
        stripe_service = StripeService(get_supabase_client())
        
        # Create a checkout session for the premium subscription
        session = stripe_service.create_checkout_session(
            tier="premium",
            customer_email="test@example.com",
            user_id="test_user_id"
        )
        
        # Print the checkout URL
        logger.info(f"Checkout URL: {session['url']}")
        print(f"Checkout URL: {session['url']}")
        
        # Update the payment link in the database
        supabase = get_supabase_client()
        response = supabase.table('saas_stripe_config').update({
            'value': session['url']
        }).eq('key', 'stripe_payment_link_premium').execute()
        
        logger.info("Updated payment link in the database")
        print("Updated payment link in the database")
        
        return session['url']
    except Exception as e:
        logger.error(f"Error creating checkout URL: {str(e)}")
        print(f"Error creating checkout URL: {str(e)}")
        return None

if __name__ == "__main__":
    create_checkout_url()
