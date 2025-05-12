#!/usr/bin/env python3
"""
Script to list all Stripe products and prices.
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

def list_stripe_products():
    """
    List all Stripe products and prices.
    """
    try:
        # Initialize the Stripe service
        stripe_service = StripeService(get_supabase_client())
        
        # Get the Stripe API key from the service
        api_key = stripe_service.api_key
        
        # Import Stripe directly
        import stripe
        stripe.api_key = api_key
        
        # List all products
        products = stripe.Product.list(limit=100, active=True)
        
        print("\n=== STRIPE PRODUCTS ===")
        for product in products.data:
            print(f"Product ID: {product.id}")
            print(f"Name: {product.name}")
            print(f"Description: {product.description}")
            print(f"Active: {product.active}")
            print(f"Created: {product.created}")
            print(f"Updated: {product.updated}")
            print(f"Metadata: {product.metadata}")
            
            # List prices for this product
            prices = stripe.Price.list(product=product.id, limit=10, active=True)
            
            print("\n  Prices:")
            for price in prices.data:
                print(f"  - Price ID: {price.id}")
                print(f"    Unit Amount: {price.unit_amount/100} {price.currency.upper()}")
                print(f"    Type: {price.type}")
                if price.type == 'recurring':
                    print(f"    Recurring: {price.recurring.interval} (every {price.recurring.interval_count} {price.recurring.interval})")
                print(f"    Active: {price.active}")
                print(f"    Created: {price.created}")
                print(f"    Metadata: {price.metadata}")
                print("")
            
            print("-" * 50)
        
        return products.data
    except Exception as e:
        logger.error(f"Error listing Stripe products: {str(e)}")
        print(f"Error listing Stripe products: {str(e)}")
        return None

if __name__ == "__main__":
    list_stripe_products()
