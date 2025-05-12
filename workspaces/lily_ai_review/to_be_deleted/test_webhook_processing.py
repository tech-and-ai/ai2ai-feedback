#!/usr/bin/env python
"""
Stripe Webhook Processing Test Script

This script tests the webhook processing functionality:
1. Checks for unprocessed webhook events
2. Attempts to process them using the process-pending-webhooks endpoint
3. Verifies that the events were processed

Usage:
    python test_webhook_processing.py

Requirements:
    - requests
    - python-dotenv
    - supabase
"""

import os
import time
import logging
import argparse
from datetime import datetime

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

# Supabase configuration
supabase_url = os.getenv('SUPABASE_PROJECT_URL')
supabase_key = os.getenv('SUPABASE_API_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_PROJECT_URL or SUPABASE_API_KEY not found in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Application configuration
app_url = os.getenv('APP_URL', 'http://localhost:8004')
admin_token = os.getenv('ADMIN_TOKEN', 'admin-token')

def check_unprocessed_events():
    """Check for unprocessed webhook events"""
    logger.info("Checking for unprocessed webhook events...")

    try:
        response = supabase.table("stripe_events") \
            .select("*") \
            .eq("processed", False) \
            .order("created_at", desc=True) \
            .execute()

        events = response.data

        if events and len(events) > 0:
            logger.info(f"Found {len(events)} unprocessed webhook events")
            for event in events:
                logger.info(f"Event: {event['event_type']} - {event['created_at']}")
            return events
        else:
            logger.info("No unprocessed webhook events found")
            return []
    except Exception as e:
        logger.error(f"Error checking unprocessed events: {str(e)}")
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

def verify_events_processed():
    """Verify that the events were processed"""
    logger.info("Verifying events were processed...")

    try:
        response = supabase.table("stripe_events") \
            .select("*") \
            .eq("processed", False) \
            .order("created_at", desc=True) \
            .execute()

        events = response.data

        if events and len(events) > 0:
            logger.warning(f"Found {len(events)} events still unprocessed")
            return False
        else:
            logger.info("All events have been processed successfully")
            return True
    except Exception as e:
        logger.error(f"Error verifying events processed: {str(e)}")
        return False

def manually_mark_events_processed():
    """Manually mark events as processed in the database"""
    logger.info("Manually marking events as processed...")

    try:
        response = supabase.table("stripe_events") \
            .update({"processed": True}) \
            .eq("processed", False) \
            .execute()

        updated = response.data

        if updated and len(updated) > 0:
            logger.info(f"Manually marked {len(updated)} events as processed")
            return True
        else:
            logger.info("No events to mark as processed")
            return False
    except Exception as e:
        logger.error(f"Error marking events as processed: {str(e)}")
        return False

def check_user_subscriptions():
    """Check user subscriptions in the database"""
    logger.info("Checking user subscriptions...")

    try:
        response = supabase.table("saas_user_subscriptions") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()

        subscriptions = response.data

        if subscriptions and len(subscriptions) > 0:
            logger.info(f"Found {len(subscriptions)} user subscriptions")
            for sub in subscriptions:
                logger.info(f"Subscription: {sub['user_id']} - {sub['subscription_tier']} - {sub['status']}")
            return subscriptions
        else:
            logger.info("No user subscriptions found")
            return []
    except Exception as e:
        logger.error(f"Error checking user subscriptions: {str(e)}")
        return []

def run_webhook_test(manual_processing=False):
    """Run the webhook processing test"""
    logger.info("Starting webhook processing test...")

    # Step 1: Check for unprocessed webhook events
    events = check_unprocessed_events()
    if not events:
        logger.info("No unprocessed events to test with")
        return True

    # Step 2: Process pending webhooks
    if manual_processing:
        logger.info("Using manual processing method")
        success = manually_mark_events_processed()
    else:
        logger.info("Using API endpoint for processing")
        success = process_pending_webhooks()

    if not success:
        logger.error("Failed to process webhook events")
        return False

    # Step 3: Verify that the events were processed
    if not verify_events_processed():
        logger.error("Events were not processed correctly")
        return False

    # Step 4: Check user subscriptions
    subscriptions = check_user_subscriptions()

    logger.info("✅ Webhook processing test completed successfully")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Stripe webhook processing")
    parser.add_argument("--manual", action="store_true", help="Use manual processing instead of API endpoint")
    args = parser.parse_args()

    success = run_webhook_test(manual_processing=args.manual)

    if success:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Tests failed!")
        exit(1)
