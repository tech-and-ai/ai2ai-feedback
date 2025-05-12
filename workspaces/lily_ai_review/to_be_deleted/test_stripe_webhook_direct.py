#!/usr/bin/env python3
"""
Test script for Stripe webhook endpoint.

This script simulates a Stripe webhook event and sends it directly to the webhook endpoint.
"""

import os
import json
import requests
import argparse
import time
from urllib.parse import urljoin

def test_webhook(base_url="http://localhost:8004", event_type="checkout.session.completed"):
    """
    Test the webhook endpoint.

    Args:
        base_url: The base URL of the application
        event_type: The type of event to simulate

    Returns:
        The response from the webhook endpoint
    """
    # Set up the webhook URL
    webhook_url = urljoin(base_url, "/billing/webhook")

    # Create a mock event based on the event type
    if event_type == "checkout.session.completed":
        # Get a real user ID from the database if possible
        real_user_id = os.environ.get("TEST_USER_ID", "test_user_123")
        real_email = os.environ.get("TEST_USER_EMAIL", "test@example.com")

        print(f"Using user ID: {real_user_id} and email: {real_email}")

        event_data = {
            "id": "evt_test_checkout_completed",
            "object": "event",
            "api_version": "2020-08-27",
            "created": int(time.time()),
            "data": {
                "object": {
                    "id": "cs_test_checkout_completed",
                    "object": "checkout.session",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "customer_details": {
                        "email": real_email
                    },
                    "metadata": {
                        "user_id": real_user_id
                    }
                }
            },
            "type": "checkout.session.completed"
        }
    else:
        print(f"Unsupported event type: {event_type}")
        return None

    # Convert the event data to JSON
    payload = json.dumps(event_data)

    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": "test_signature"
    }

    # Send the webhook event
    print(f"Sending {event_type} event to {webhook_url}...")
    try:
        response = requests.post(webhook_url, headers=headers, data=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        return response
    except Exception as e:
        print(f"Error sending webhook event: {str(e)}")
        return None

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Test Stripe webhook endpoint")
    parser.add_argument("--base-url", default="http://localhost:8004", help="The base URL of the application")
    parser.add_argument("--event-type", default="checkout.session.completed", help="The type of event to simulate")
    args = parser.parse_args()

    # Test the webhook endpoint
    test_webhook(args.base_url, args.event_type)

if __name__ == "__main__":
    main()
