import logging
import traceback
import os
from app.services.billing.stripe_service import StripeService
from app.utils.supabase_client import get_supabase_client
import stripe

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_checkout_session():
    print("Starting test...")
    
    try:
        # Initialize Stripe service
        service = StripeService(get_supabase_client())
        print("Service initialized")
        
        # Get the current price ID for premium
        print(f"Current premium price ID: {service.premium_price_id}")
        
        # Check the price in Stripe
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        price = stripe.Price.retrieve(service.premium_price_id)
        print(f"Price details: {price}")
        print(f"Amount: {price.unit_amount / 100} {price.currency}")
        
        # Create checkout session
        session = service.create_checkout_session(
            tier='premium',
            customer_email='test@example.com',
            user_id='test_user_id'
        )
        
        # Print result
        print(f"Checkout URL: {session.get('url', 'No URL found')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_checkout_session()
