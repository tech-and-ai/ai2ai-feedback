#!/usr/bin/env python3
"""
Direct script to test email notifications by calling Supabase Edge Functions.
"""

import os
import sys
import uuid
import json
import time
import logging
import requests
from datetime import datetime

# Supabase project details
SUPABASE_URL = "https://brxpkhpkitfzecvmwzgz.supabase.co"
# You'll need to provide the service key when running the script
SERVICE_KEY = None  # Will be provided as command line argument

# User ID to send notifications to
USER_ID = "55b4ec8c-2cf5-40fe-8718-75fe45f49a69"  # pantaleone@btinternet.com

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def call_edge_function(function_name, payload):
    """Call a Supabase Edge Function."""
    url = f"{SUPABASE_URL}/functions/v1/{function_name}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SERVICE_KEY}"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Error calling {function_name}: {response.status_code} - {response.text}")
        return None

def test_welcome_email():
    """Test the welcome email notification."""
    logger.info("Testing welcome email notification...")
    
    result = call_edge_function("notify", {
        "event_type": "email.verified",
        "user_id": USER_ID,
        "data": {}
    })
    
    if result and result.get("success"):
        logger.info("Welcome email notification sent successfully")
    else:
        logger.error("Failed to send welcome email notification")

def test_paper_queued():
    """Test the paper queued notification."""
    logger.info("Testing paper queued notification...")
    
    paper_id = str(uuid.uuid4())
    
    result = call_edge_function("paper-notifications", {
        "paper_id": paper_id,
        "event_type": "paper.queued"
    })
    
    if result and result.get("success"):
        logger.info("Paper queued notification sent successfully")
    else:
        logger.error("Failed to send paper queued notification")
    
    return paper_id

def test_paper_started(paper_id):
    """Test the paper started notification."""
    logger.info("Testing paper started notification...")
    
    result = call_edge_function("paper-notifications", {
        "paper_id": paper_id,
        "event_type": "paper.started"
    })
    
    if result and result.get("success"):
        logger.info("Paper started notification sent successfully")
    else:
        logger.error("Failed to send paper started notification")

def test_paper_completed(paper_id):
    """Test the paper completed notification."""
    logger.info("Testing paper completed notification...")
    
    result = call_edge_function("paper-notifications", {
        "paper_id": paper_id,
        "event_type": "paper.completed"
    })
    
    if result and result.get("success"):
        logger.info("Paper completed notification sent successfully")
    else:
        logger.error("Failed to send paper completed notification")

def test_paper_failed():
    """Test the paper failed notification."""
    logger.info("Testing paper failed notification...")
    
    paper_id = str(uuid.uuid4())
    
    result = call_edge_function("paper-notifications", {
        "paper_id": paper_id,
        "event_type": "paper.failed",
        "error_message": "This is a test error message for notification testing"
    })
    
    if result and result.get("success"):
        logger.info("Paper failed notification sent successfully")
    else:
        logger.error("Failed to send paper failed notification")

def main():
    """Main function to test email notifications."""
    if len(sys.argv) < 2:
        print("Usage: python direct_email_test.py <service_key>")
        return 1
    
    global SERVICE_KEY
    SERVICE_KEY = sys.argv[1]
    
    # Test welcome email
    test_welcome_email()
    time.sleep(2)
    
    # Test paper notifications
    paper_id = test_paper_queued()
    time.sleep(2)
    
    test_paper_started(paper_id)
    time.sleep(2)
    
    test_paper_completed(paper_id)
    time.sleep(2)
    
    test_paper_failed()
    
    logger.info("All email notifications have been triggered")
    return 0

if __name__ == "__main__":
    sys.exit(main())
