#!/usr/bin/env python3
"""
Test script for Stripe success page.

This script simulates a successful payment and tests the redirect.
"""

import os
import requests
import argparse
from urllib.parse import urljoin

def test_success_page(base_url="http://localhost:8004", session_id="cs_test_success"):
    """
    Test the success page.

    Args:
        base_url: The base URL of the application
        session_id: The session ID to use

    Returns:
        The response from the success page
    """
    # Set up the success URL
    success_url = urljoin(base_url, f"/billing/success?session_id={session_id}")

    # Set up cookies for authentication
    # This is a simplified example - in a real test, you would need to authenticate first
    cookies = {
        "session": "test_session"
    }

    # Set up HTTP Basic Authentication credentials
    auth = ("admin", "Leoisking")  # Your actual username and password

    # Send the request
    print(f"Sending request to {success_url} with HTTP Basic Auth...")
    try:
        response = requests.get(
            success_url,
            cookies=cookies,
            auth=auth,  # Include HTTP Basic Auth
            allow_redirects=False
        )
        print(f"Response status code: {response.status_code}")

        if response.status_code == 303:
            print(f"Redirect location: {response.headers.get('Location')}")
            print("Success! The redirect is working correctly.")
        elif response.status_code == 307:
            print(f"Temporary redirect to: {response.headers.get('Location')}")
            print("This is likely due to session handling or authentication issues.")
        else:
            print("Error: The redirect is not working correctly.")
            print(f"Response body: {response.text}")

        return response
    except Exception as e:
        print(f"Error sending request: {str(e)}")
        return None

def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description="Test Stripe success page")
    parser.add_argument("--base-url", default="http://localhost:8004", help="The base URL of the application")
    parser.add_argument("--session-id", default="cs_test_success", help="The session ID to use")
    args = parser.parse_args()

    # Test the success page
    test_success_page(args.base_url, args.session_id)

if __name__ == "__main__":
    main()
