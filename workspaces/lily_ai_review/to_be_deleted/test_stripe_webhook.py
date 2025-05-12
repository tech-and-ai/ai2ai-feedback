#!/usr/bin/env python3
"""
Test script for Stripe webhook handling.

This script simulates a Stripe webhook event to test the webhook handler.
"""

import os
import json
import requests
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def simulate_webhook_event(event_type, local_server=True):
    """
    Simulate a Stripe webhook event.
    
    Args:
        event_type: The type of event to simulate (e.g., checkout.session.completed)
        local_server: Whether to send to local server or production
        
    Returns:
        The response from the webhook handler
    """
    # Set up the webhook URL
    if local_server:
        webhook_url = "http://localhost:8004/billing/webhook"
    else:
        webhook_url = "https://lilyai.app/billing/webhook"
    
    # Create a mock event based on the event type
    if event_type == "checkout.session.completed":
        event_data = {
            "id": "evt_test_checkout_completed",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1630000000,
            "data": {
                "object": {
                    "id": "cs_test_checkout_completed",
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
    elif event_type == "customer.subscription.updated":
        event_data = {
            "id": "evt_test_subscription_updated",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1630000000,
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "object": "subscription",
                    "customer": "cus_test_123",
                    "status": "active",
                    "current_period_end": 1640000000,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_test_123"
                                }
                            }
                        ]
                    }
                }
            },
            "type": "customer.subscription.updated"
        }
    elif event_type == "customer.subscription.deleted":
        event_data = {
            "id": "evt_test_subscription_deleted",
            "object": "event",
            "api_version": "2020-08-27",
            "created": 1630000000,
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "object": "subscription",
                    "customer": "cus_test_123",
                    "status": "canceled",
                    "current_period_end": 1640000000,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_test_123"
                                }
                            }
                        ]
                    }
                }
            },
            "type": "customer.subscription.deleted"
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
    parser = argparse.ArgumentParser(description="Test Stripe webhook handling")
    parser.add_argument("event_type", choices=["checkout.session.completed", "customer.subscription.updated", "customer.subscription.deleted"], help="The type of event to simulate")
    parser.add_argument("--production", action="store_true", help="Send to production server instead of local")
    args = parser.parse_args()
    
    # Simulate the webhook event
    simulate_webhook_event(args.event_type, not args.production)

if __name__ == "__main__":
    main()
