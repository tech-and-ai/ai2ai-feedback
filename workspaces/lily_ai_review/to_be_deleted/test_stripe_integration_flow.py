#!/usr/bin/env python
"""
Stripe Integration Test Script

This script tests the complete Stripe subscription flow:
1. Creates a test customer
2. Creates a test subscription
3. Verifies webhook processing
4. Checks database updates

Usage:
    python test_stripe_integration_flow.py

Requirements:
    - stripe
    - requests
    - python-dotenv
    - supabase
"""

import os
import time
import json
import uuid
import logging
import argparse
from datetime import datetime, timedelta

import stripe
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
if not stripe.api_key:
    raise ValueError("STRIPE_SECRET_KEY not found in environment variables")

# Supabase configuration
supabase_url = os.getenv('SUPABASE_PROJECT_URL')
supabase_key = os.getenv('SUPABASE_API_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_PROJECT_URL or SUPABASE_API_KEY not found in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Application configuration
app_url = os.getenv('APP_URL', 'http://localhost:8004')
admin_token = os.getenv('ADMIN_TOKEN', 'admin-token')

def create_test_customer():
    """Create a test customer in Stripe"""
    logger.info("Creating test customer in Stripe...")

    # Generate a unique email to avoid conflicts
    email = f"test-{uuid.uuid4()}@example.com"
    name = f"Test User {uuid.uuid4().hex[:8]}"

    try:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={
                "test": "true",
                "created_by": "integration_test"
            }
        )
        logger.info(f"Created test customer: {customer.id} ({email})")
        return customer
    except Exception as e:
        logger.error(f"Error creating test customer: {str(e)}")
        raise

def create_test_subscription(customer_id, price_id=None):
    """Create a test subscription for the customer"""
    logger.info(f"Creating test subscription for customer {customer_id}...")

    # If no price_id is provided, get the premium subscription price
    if not price_id:
        price_id = os.getenv('STRIPE_PREMIUM_PRICE_ID')
        if not price_id:
            # List prices and find a subscription price
            prices = stripe.Price.list(active=True, type="recurring", limit=1)
            if not prices.data:
                # Create a test product and price if none exists
                logger.info("No subscription prices found, creating test product and price...")
                product = stripe.Product.create(
                    name="Test Premium Plan",
                    description="Test Premium Plan for integration testing"
                )
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=1800,  # $18.00
                    currency="usd",
                    recurring={"interval": "month"}
                )
                price_id = price.id
            else:
                price_id = prices.data[0].id

    try:
        # Create the subscription
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={
                "test": "true",
                "created_by": "integration_test",
                "tier": "premium",
                "papers_limit": "10"
            },
            expand=["latest_invoice.payment_intent"]
        )

        logger.info(f"Created test subscription: {subscription.id}")
        return subscription
    except Exception as e:
        logger.error(f"Error creating test subscription: {str(e)}")
        raise

def check_webhook_events(event_types, max_attempts=10, delay=2):
    """Check if webhook events were received and processed"""
    logger.info(f"Checking for webhook events: {event_types}...")

    for attempt in range(max_attempts):
        try:
            # Query the stripe_events table
            response = supabase.table("stripe_events") \
                .select("*") \
                .in_("event_type", event_types) \
                .order("created_at", desc=True) \
                .limit(len(event_types)) \
                .execute()

            events = response.data

            if events and len(events) > 0:
                logger.info(f"Found {len(events)} webhook events")
                return events

            logger.info(f"No webhook events found yet, attempt {attempt+1}/{max_attempts}")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error checking webhook events: {str(e)}")
            time.sleep(delay)

    logger.warning(f"No webhook events found after {max_attempts} attempts")
    return []

def process_pending_webhooks():
    """Process any pending webhook events"""
    logger.info("Processing pending webhook events...")

    try:
        response = requests.get(
            f"{app_url}/billing/process-pending-webhooks",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully processed webhook events: {result}")
            return True
        else:
            logger.error(f"Error processing webhook events: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception processing webhook events: {str(e)}")
        return False

def check_user_subscription(user_id):
    """Check if the user's subscription was updated in the database"""
    logger.info(f"Checking subscription for user {user_id}...")

    try:
        response = supabase.table("saas_user_subscriptions") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if response.data and len(response.data) > 0:
            subscription = response.data[0]
            logger.info(f"Found subscription: {subscription}")
            return subscription
        else:
            logger.warning(f"No subscription found for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error checking user subscription: {str(e)}")
        return None

def create_test_user():
    """Create a test user in the database"""
    logger.info("Creating test user in database...")

    # Generate a unique email and user ID
    email = f"test-{uuid.uuid4()}@example.com"
    user_id = str(uuid.uuid4())

    try:
        # Insert user into saas_users table
        response = supabase.table("saas_users") \
            .insert({
                "id": user_id,
                "email": email,
                "name": f"Test User {uuid.uuid4().hex[:8]}",
                "subscription_tier": "free",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }) \
            .execute()

        if response.data and len(response.data) > 0:
            logger.info(f"Created test user: {user_id} ({email})")
            return response.data[0]
        else:
            logger.error("Failed to create test user")
            return None
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        return None

def link_customer_to_user(customer_id, user_id):
    """Link a Stripe customer to a user in the database"""
    logger.info(f"Linking customer {customer_id} to user {user_id}...")

    try:
        # Update the customer metadata
        stripe.Customer.modify(
            customer_id,
            metadata={"user_id": user_id}
        )

        logger.info(f"Updated customer metadata with user_id: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error linking customer to user: {str(e)}")
        return False

def run_integration_test():
    """Run the complete integration test"""
    logger.info("Starting Stripe integration test...")

    # Step 1: Create a test user in our database
    user = create_test_user()
    if not user:
        logger.error("Failed to create test user, aborting test")
        return False

    user_id = user["id"]

    # Step 2: Create a test customer in Stripe
    customer = create_test_customer()
    if not customer:
        logger.error("Failed to create test customer, aborting test")
        return False

    # Step 3: Link the customer to the user
    if not link_customer_to_user(customer.id, user_id):
        logger.error("Failed to link customer to user, aborting test")
        return False

    # Step 4: Create a test subscription
    subscription = create_test_subscription(customer.id)
    if not subscription:
        logger.error("Failed to create test subscription, aborting test")
        return False

    # Step 5: Wait for webhook events
    events = check_webhook_events(["customer.subscription.created"])

    # Step 6: Process pending webhooks
    process_pending_webhooks()

    # Step 7: Check if the user's subscription was updated
    subscription_record = check_user_subscription(user_id)

    # Step 8: Verify the results
    if subscription_record and subscription_record["subscription_tier"] == "premium":
        logger.info("✅ Integration test PASSED: User subscription was updated correctly")
        return True
    else:
        logger.error("❌ Integration test FAILED: User subscription was not updated correctly")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Stripe integration flow")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test data after running")
    args = parser.parse_args()

    success = run_integration_test()

    if args.cleanup and success:
        logger.info("Cleaning up test data...")
        # Add cleanup code here if needed

    if success:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Tests failed!")
        exit(1)
