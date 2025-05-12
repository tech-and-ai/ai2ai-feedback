#!/usr/bin/env python3
"""
Test script for email notifications via Supabase Edge Functions.

This script tests the email notification system by:
1. Creating a test paper
2. Updating its status to trigger notifications
3. Verifying the notifications were sent
"""

import os
import sys
import json
import time
import uuid
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import supabase

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create Supabase client
def get_supabase_client():
    """Get Supabase client from environment variables."""
    # Load environment variables
    load_dotenv()

    # Get Supabase URL and key
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

    # Create client
    client = supabase.create_client(supabase_url, supabase_key)
    return client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_paper(db, user_id):
    """Create a test paper for notification testing."""
    paper_id = str(uuid.uuid4())

    # Create paper data
    paper_data = {
        "id": paper_id,
        "user_id": user_id,
        "title": f"Test Paper {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "topic": "Email Notification Testing",
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Insert paper into database
    result = db.table("papers").insert(paper_data).execute()

    if not result.data:
        logger.error("Failed to create test paper")
        return None

    logger.info(f"Created test paper with ID: {paper_id}")
    return paper_id

def update_paper_status(db, paper_id, status, error_message=None):
    """Update paper status to trigger notifications."""
    # Prepare payload for Edge Function
    payload = {
        "paper_id": paper_id,
        "status": status
    }

    # Add error message if status is failed
    if status == "failed" and error_message:
        payload["error_message"] = error_message

    # Add storage URLs if status is completed
    if status == "completed":
        payload["storage_urls"] = {
            "pdf": f"https://researchassistant.uk/papers/{paper_id}/download/pdf",
            "docx": f"https://researchassistant.uk/papers/{paper_id}/download/docx"
        }
        payload["word_count"] = 2500

    # Call Edge Function
    try:
        result = db.functions.invoke(
            "update-paper-status",
            invoke_options={"body": payload}
        )

        if result and result.get("success") is True:
            logger.info(f"Paper status updated to '{status}' via Edge Function")
            return True
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Failed to update paper status: {error}")
            return False
    except Exception as e:
        logger.error(f"Error calling Edge Function: {str(e)}")
        return False

def check_notification_logs(db, paper_id, event_type):
    """Check if notification was logged."""
    # Get paper details to find user_id
    paper_result = db.table("papers").select("user_id").eq("id", paper_id).execute()

    if not paper_result.data:
        logger.error(f"Paper {paper_id} not found")
        return False

    user_id = paper_result.data[0]["user_id"]

    # Check notification logs
    logs_result = db.table("saas_notification_logs").select("*").eq("user_id", user_id).eq("event_type", event_type).execute()

    if logs_result.data:
        logger.info(f"Found notification log for event {event_type}")
        return True
    else:
        logger.warning(f"No notification log found for event {event_type}")
        return False

def main():
    """Main function to test email notifications."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test email notifications")
    parser.add_argument("--user-id", required=True, help="User ID to send notifications to")
    parser.add_argument("--delay", type=int, default=5, help="Delay between status updates (seconds)")
    args = parser.parse_args()

    # Get Supabase client
    db = get_supabase_client()

    # Create test paper
    paper_id = create_test_paper(db, args.user_id)
    if not paper_id:
        logger.error("Failed to create test paper, exiting")
        return 1

    # Wait for initial notification to be sent
    logger.info(f"Waiting {args.delay} seconds for initial notification...")
    time.sleep(args.delay)

    # Check if queued notification was sent
    check_notification_logs(db, paper_id, "paper.queued")

    # Update paper status to processing
    logger.info("Updating paper status to 'processing'...")
    if not update_paper_status(db, paper_id, "processing"):
        logger.error("Failed to update paper status to 'processing'")
        return 1

    # Wait for processing notification to be sent
    logger.info(f"Waiting {args.delay} seconds for processing notification...")
    time.sleep(args.delay)

    # Check if processing notification was sent
    check_notification_logs(db, paper_id, "paper.started")

    # Update paper status to completed
    logger.info("Updating paper status to 'completed'...")
    if not update_paper_status(db, paper_id, "completed"):
        logger.error("Failed to update paper status to 'completed'")
        return 1

    # Wait for completed notification to be sent
    logger.info(f"Waiting {args.delay} seconds for completed notification...")
    time.sleep(args.delay)

    # Check if completed notification was sent
    check_notification_logs(db, paper_id, "paper.completed")

    # Create another test paper for failure testing
    logger.info("Creating another test paper for failure testing...")
    paper_id = create_test_paper(db, args.user_id)
    if not paper_id:
        logger.error("Failed to create test paper for failure testing")
        return 1

    # Update paper status to failed
    logger.info("Updating paper status to 'failed'...")
    if not update_paper_status(db, paper_id, "failed", "Test error message for notification testing"):
        logger.error("Failed to update paper status to 'failed'")
        return 1

    # Wait for failed notification to be sent
    logger.info(f"Waiting {args.delay} seconds for failed notification...")
    time.sleep(args.delay)

    # Check if failed notification was sent
    check_notification_logs(db, paper_id, "paper.failed")

    logger.info("Email notification testing completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
