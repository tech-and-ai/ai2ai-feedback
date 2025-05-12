#!/usr/bin/env python3
"""
Test script for Stripe API.

This script tests the Stripe API directly to verify that your API keys are working.
"""

import stripe
from test_config import config

# Set up Stripe API key
stripe.api_key = config.api_key

# Validate configuration
errors = config.validate()
if errors:
    print("❌ Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

def test_list_customers():
    """Test listing customers."""
    print("Testing list customers...")
    try:
        customers = stripe.Customer.list(limit=3)
        print(f"✅ Successfully listed customers. Found {len(customers.data)} customers.")
        for customer in customers.data:
            print(f"  - {customer.id}: {customer.email}")
        return True
    except Exception as e:
        print(f"❌ Error listing customers: {str(e)}")
        return False

def test_list_products():
    """Test listing products."""
    print("Testing list products...")
    try:
        products = stripe.Product.list(limit=3, active=True)
        print(f"✅ Successfully listed products. Found {len(products.data)} products.")
        for product in products.data:
            print(f"  - {product.id}: {product.name}")
        return True
    except Exception as e:
        print(f"❌ Error listing products: {str(e)}")
        return False

def test_list_prices():
    """Test listing prices."""
    print("Testing list prices...")
    try:
        prices = stripe.Price.list(limit=3, active=True)
        print(f"✅ Successfully listed prices. Found {len(prices.data)} prices.")
        for price in prices.data:
            amount = price.unit_amount / 100 if price.unit_amount else "N/A"
            print(f"  - {price.id}: {amount} {price.currency}")
        return True
    except Exception as e:
        print(f"❌ Error listing prices: {str(e)}")
        return False

def test_create_checkout_session():
    """Test creating a checkout session."""
    print("Testing create checkout session...")
    try:
        # Get the premium price ID from configuration
        price_id = config.premium_price_id
        if not price_id:
            print("❌ Premium price ID not set in configuration")
            return False

        # Create a checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=config.success_url,
            cancel_url=config.cancel_url,
            metadata={
                "user_id": "test_user_123"
            }
        )
        print(f"✅ Successfully created checkout session: {session.id}")
        print(f"Checkout URL: {session.url}")

        # Print instructions for testing
        print("\nTo test the payment flow:")
        print("1. Open the checkout URL in your browser")
        print("2. Use test card number: 4242 4242 4242 4242")
        print("3. Use any future date for expiry and any 3 digits for CVC")
        print("4. Use any name and address")
        print("5. After payment, you should be redirected to the success page")

        return True
    except Exception as e:
        print(f"❌ Error creating checkout session: {str(e)}")
        return False

def main():
    """Run the tests."""
    print("=== Testing Stripe API ===")

    # Check API key
    if not stripe.api_key:
        print("❌ STRIPE_API_KEY not set in .env file")
        return

    print(f"Using API key: {stripe.api_key[:4]}...{stripe.api_key[-4:]}")

    # Run tests
    tests = [
        test_list_customers,
        test_list_products,
        test_list_prices,
        test_create_checkout_session
    ]

    success_count = 0
    for test in tests:
        if test():
            success_count += 1
        print()

    print(f"=== Tests completed: {success_count}/{len(tests)} successful ===")

if __name__ == "__main__":
    main()
