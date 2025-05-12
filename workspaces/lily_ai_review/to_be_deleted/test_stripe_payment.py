#!/usr/bin/env python3
"""
Test script for Stripe payment flow.

This script creates a checkout session and opens it in the browser.
"""

import os
import json
import stripe
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_checkout_session():
    """
    Create a checkout session for testing.

    Returns:
        The checkout session URL
    """
    # Set up Stripe API key
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    print(f"Using Stripe API key: {stripe.api_key[:4]}...{stripe.api_key[-4:] if stripe.api_key else 'None'}")

    if not stripe.api_key:
        print("STRIPE_SECRET_KEY environment variable not set")
        return None

    # Get the premium price ID
    price_id = os.environ.get("STRIPE_PREMIUM_PRICE_ID")
    print(f"Using price ID: {price_id}")

    if not price_id:
        print("STRIPE_PREMIUM_PRICE_ID environment variable not set")
        return None

    # Get the base URL
    base_url = os.environ.get("BASE_URL", "http://localhost:8004")

    # Create a checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/billing/cancel",
            metadata={
                "user_id": os.environ.get("TEST_USER_ID", "")
            }
        )

        print(f"Checkout session created: {session.id}")
        print(f"Checkout URL: {session.url}")

        return session.url
    except Exception as e:
        print(f"Error creating checkout session: {str(e)}")
        return None

def main():
    """Run the script."""
    # Create a checkout session
    checkout_url = create_checkout_session()

    if checkout_url:
        # Open the checkout URL in the browser
        print(f"Opening checkout URL in browser: {checkout_url}")
        webbrowser.open(checkout_url)

        print("\nTo test the payment flow:")
        print("1. Complete the payment using test card number: 4242 4242 4242 4242")
        print("2. Use any future date for expiry and any 3 digits for CVC")
        print("3. Use any name and address")
        print("4. After payment, you should be redirected to the success page")

if __name__ == "__main__":
    main()
