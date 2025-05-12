#!/usr/bin/env python3
"""
Test script for Stripe webhook.

This script simulates a Stripe webhook event and sends it to the webhook endpoint.
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook(base_url="http://localhost:8004"):
    """
    Test the webhook endpoint.

    Args:
        base_url: The base URL of the application

    Returns:
        The response from the webhook endpoint
    """
    # Set up the webhook URL
    webhook_url = f"{base_url}/billing/webhook"

    # Create a mock checkout.session.completed event
    event_data = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2020-08-27",
        "created": int(time.time()),
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "customer": f"cus_test_{int(time.time())}",
                "subscription": f"sub_test_{int(time.time())}",
                "customer_details": {
                    "email": os.environ.get("TEST_USER_EMAIL", "test@example.com")
                },
                "metadata": {
                    "user_id": os.environ.get("TEST_USER_ID", "")
                }
            }
        }
    }

    # Convert the event data to JSON
    payload = json.dumps(event_data)

    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": "test_signature",
        "X-Bypass-Verification": "true"  # Custom header to bypass verification in development
    }

    # Send the webhook event
    print(f"Sending webhook event to {webhook_url}...")
    print(f"Event data: {json.dumps(event_data, indent=2)}")
    print(f"Headers: {headers}")

    try:
        # Use requests.Session for better debugging
        session = requests.Session()
        session.trust_env = False  # Disable proxy settings

        # Send the request with verbose output
        print(f"Sending POST request to {webhook_url}...")
        response = session.post(webhook_url, headers=headers, data=payload)

        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")

        return response
    except Exception as e:
        print(f"Error sending webhook event: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    """Run the script."""
    # Get the base URL from environment or use default
    base_url = os.environ.get("BASE_URL", "http://localhost:8004")

    # Test the webhook endpoint
    test_webhook(base_url)

if __name__ == "__main__":
    main()
