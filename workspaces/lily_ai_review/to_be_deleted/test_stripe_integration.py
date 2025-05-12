#!/usr/bin/env python3
"""
Test script for Stripe integration.

This script tests the Stripe integration by:
1. Creating a test customer
2. Creating a test checkout session
3. Simulating a webhook event
"""

import os
import json
import stripe
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Stripe API key
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Set up webhook secret
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Set up base URL
base_url = "http://localhost:8004"

def test_create_customer():
    """Test creating a Stripe customer."""
    print("Testing customer creation...")
    try:
        customer = stripe.Customer.create(
            email="test@example.com",
            name="Test User"
        )
        print(f"✅ Successfully created customer: {customer.id}")
        return customer
    except Exception as e:
        print(f"❌ Error creating customer: {str(e)}")
        return None

def test_create_checkout_session(customer_id):
    """Test creating a checkout session."""
    print("Testing checkout session creation...")
    try:
        # Get the premium price ID
        price_id = os.getenv("STRIPE_PRICE_ID_PREMIUM")
        
        # Create a checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/billing/cancel",
            metadata={
                "user_id": "test_user_123"
            }
        )
        print(f"✅ Successfully created checkout session: {session.id}")
        print(f"Checkout URL: {session.url}")
        return session
    except Exception as e:
        print(f"❌ Error creating checkout session: {str(e)}")
        return None

def test_webhook_event(session_id):
    """Test simulating a webhook event."""
    print("Testing webhook event simulation...")
    try:
        # Create a mock checkout.session.completed event
        event_data = {
            "id": f"evt_test_{session_id}",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1630000000,
            "data": {
                "object": {
                    "id": session_id,
                    "object": "checkout.session",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "customer_details": {
                        "email": "test@example.com"
                    },
                    "metadata": {
                        "user_id": "test_user_123"
                    }
                }
            },
            "type": "checkout.session.completed"
        }
        
        # Sign the event
        payload = json.dumps(event_data)
        
        # Send the webhook event to the server
        response = requests.post(
            f"{base_url}/billing/webhook",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "test_signature"
            },
            data=payload
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully sent webhook event: {response.json()}")
        else:
            print(f"❌ Error sending webhook event: {response.status_code} - {response.text}")
        
        return response
    except Exception as e:
        print(f"❌ Error simulating webhook event: {str(e)}")
        return None

def main():
    """Run the tests."""
    print("=== Testing Stripe Integration ===")
    
    # Test creating a customer
    customer = test_create_customer()
    if not customer:
        return
    
    # Test creating a checkout session
    session = test_create_checkout_session(customer.id)
    if not session:
        return
    
    # Test simulating a webhook event
    test_webhook_event(session.id)
    
    print("=== Tests Complete ===")
    print("Note: For a complete test, use the Stripe CLI to forward webhooks:")
    print("./stripe_cli_setup.sh")

if __name__ == "__main__":
    main()
