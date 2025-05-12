#!/usr/bin/env python3
"""
Test script for subscription service.

This script tests the subscription service directly.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_subscription_status(base_url="http://localhost:8004"):
    """
    Test the subscription status endpoint.
    
    Args:
        base_url: The base URL of the application
        
    Returns:
        The response from the subscription status endpoint
    """
    # Set up the subscription status URL
    status_url = f"{base_url}/billing/status"
    
    # Get the session cookie from the environment
    session_cookie = os.environ.get("SESSION_COOKIE")
    if not session_cookie:
        print("SESSION_COOKIE environment variable not set")
        return None
    
    # Set up cookies
    cookies = {"session": session_cookie}
    
    # Set up HTTP Basic Auth
    auth = ("admin", "Leoisking")
    
    # Send the request
    print(f"Sending request to {status_url}...")
    try:
        response = requests.get(status_url, cookies=cookies, auth=auth)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        return response
    except Exception as e:
        print(f"Error sending request: {str(e)}")
        return None

def main():
    """Run the script."""
    # Get the base URL from environment or use default
    base_url = os.environ.get("BASE_URL", "http://localhost:8004")
    
    # Test the subscription status endpoint
    test_subscription_status(base_url)

if __name__ == "__main__":
    main()
