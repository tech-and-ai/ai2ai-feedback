import logging
import traceback
from app.services.billing.stripe_service import StripeService
from app.utils.supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_checkout_session():
    print("Starting test...")
    
    try:
        # Initialize Stripe service
        service = StripeService(get_supabase_client())
        print("Service initialized")
        
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
