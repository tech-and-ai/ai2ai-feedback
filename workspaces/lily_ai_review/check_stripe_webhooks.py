#!/usr/bin/env python
"""
Script to check Stripe webhook configurations.
"""
import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Stripe API key from environment
stripe_api_key = os.getenv("STRIPE_API_KEY")
if not stripe_api_key:
    print("Error: STRIPE_API_KEY not found in environment variables")
    exit(1)

# Configure Stripe with API key
stripe.api_key = stripe_api_key

def list_webhooks():
    """List all webhooks in the Stripe account."""
    try:
        webhooks = stripe.WebhookEndpoint.list()
        print("\nCurrent webhooks:")
        if not webhooks.data:
            print("No webhooks found")
        for webhook in webhooks.data:
            print(f"ID: {webhook.id}")
            print(f"URL: {webhook.url}")
            print(f"Status: {webhook.status}")
            print(f"Events: {', '.join(webhook.enabled_events)}")
            print("-" * 50)
        return webhooks.data
    except Exception as e:
        print(f"Error listing webhooks: {str(e)}")
        return []

if __name__ == "__main__":
    print("Stripe Webhook Checker")
    print("=" * 50)
    
    # List current webhooks
    webhooks = list_webhooks()
