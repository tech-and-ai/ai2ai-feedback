#!/usr/bin/env python3
"""
Script to directly trigger email notifications via Supabase Edge Functions.
"""

import os
import sys
import uuid
import json
import time
import logging
import requests
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def trigger_notification(supabase_url, service_key, user_id, event_type, data=None):
    """Trigger a notification via the notify Edge Function."""
    url = f"{supabase_url}/functions/v1/notify"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {service_key}"
    }
    
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "data": data or {}
    }
    
    logger.info(f"Triggering notification: {event_type}")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        logger.info(f"Successfully triggered {event_type} notification")
        return True
    else:
        logger.error(f"Failed to trigger {event_type} notification: {response.status_code} - {response.text}")
        return False

def trigger_paper_notification(supabase_url, service_key, user_id, delay=3):
    """Trigger all paper-related notifications."""
    # Create a test paper in the database
    paper_id = str(uuid.uuid4())
    
    # Create paper data for notifications
    paper_data = {
        "paper": {
            "id": paper_id,
            "title": f"Test Paper {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "topic": "Email Notification Testing",
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }
    }
    
    # Trigger paper.queued notification
    trigger_notification(supabase_url, service_key, user_id, "paper.queued", paper_data)
    logger.info(f"Waiting {delay} seconds...")
    time.sleep(delay)
    
    # Update paper data for processing notification
    paper_data["paper"]["status"] = "processing"
    trigger_notification(supabase_url, service_key, user_id, "paper.started", paper_data)
    logger.info(f"Waiting {delay} seconds...")
    time.sleep(delay)
    
    # Update paper data for completed notification
    paper_data["paper"]["status"] = "completed"
    paper_data["paper"]["completed_at"] = datetime.now().isoformat()
    paper_data["paper"]["view_link"] = f"https://researchassistant.uk/papers/{paper_id}"
    paper_data["paper"]["download_links"] = {
        "pdf": f"https://researchassistant.uk/papers/{paper_id}/download/pdf",
        "docx": f"https://researchassistant.uk/papers/{paper_id}/download/docx"
    }
    trigger_notification(supabase_url, service_key, user_id, "paper.completed", paper_data)
    logger.info(f"Waiting {delay} seconds...")
    time.sleep(delay)
    
    # Create another test paper for failure notification
    paper_id = str(uuid.uuid4())
    paper_data = {
        "paper": {
            "id": paper_id,
            "title": f"Failed Test Paper {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "topic": "Email Notification Testing - Failure Case",
            "status": "failed",
            "created_at": datetime.now().isoformat()
        },
        "error": {
            "message": "This is a test error message for notification testing"
        }
    }
    trigger_notification(supabase_url, service_key, user_id, "paper.failed", paper_data)

def main():
    """Main function to trigger email notifications."""
    parser = argparse.ArgumentParser(description="Trigger email notifications")
    parser.add_argument("--user-id", required=True, help="User ID to send notifications to")
    parser.add_argument("--supabase-url", required=True, help="Supabase URL")
    parser.add_argument("--service-key", required=True, help="Supabase service role key")
    parser.add_argument("--delay", type=int, default=3, help="Delay between notifications (seconds)")
    args = parser.parse_args()
    
    # Trigger paper notifications
    trigger_paper_notification(args.supabase_url, args.service_key, args.user_id, args.delay)
    
    logger.info("All notifications triggered successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
