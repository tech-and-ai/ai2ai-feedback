import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Stripe API key
stripe.api_key = os.getenv('STRIPE_API_KEY')

try:
    # Create a recurring price
    price = stripe.Price.create(
        unit_amount=1800,  # £18.00
        currency='gbp',
        recurring={'interval': 'month'},
        product='prod_SHS5MyqtEeeSDJ'
    )
    
    print(f'Created recurring price: {price.id}')
    print(f'Amount: {price.unit_amount / 100} {price.currency}')
    print(f'Recurring: {price.recurring}')
    
except Exception as e:
    print(f'Error: {str(e)}')
    import traceback
    print(traceback.format_exc())
