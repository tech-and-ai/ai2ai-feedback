#!/usr/bin/env python3
"""
Script to monitor the discussion monitor page for new messages
"""

import asyncio
import json
import logging
import time
import os
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
MONITOR_URL = "http://localhost:8090/discussion_monitor.html"
CHECK_INTERVAL = 5  # seconds

# File to store the last seen message
LAST_SEEN_FILE = "last_seen_message.json"

def get_last_seen_message():
    """Get the last seen message from the file."""
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading last seen message: {e}")
    return None

def save_last_seen_message(message):
    """Save the last seen message to the file."""
    try:
        with open(LAST_SEEN_FILE, "w") as f:
            json.dump(message, f)
    except Exception as e:
        logger.error(f"Error saving last seen message: {e}")

def check_for_new_messages():
    """Check for new messages in the discussion monitor."""
    try:
        # Get the HTML content of the page
        response = requests.get(MONITOR_URL)
        if response.status_code != 200:
            logger.error(f"Error getting page: {response.status_code}")
            return
        
        # Extract the messages from the HTML
        html = response.text
        
        # Look for the discussionData variable
        start_index = html.find("discussionData = ")
        if start_index == -1:
            logger.error("Could not find discussionData in the HTML")
            return
        
        # Extract the JSON data
        start_index = html.find("{", start_index)
        end_index = html.find("};", start_index)
        if start_index == -1 or end_index == -1:
            logger.error("Could not extract JSON data from the HTML")
            return
        
        json_data = html[start_index:end_index+1]
        
        # Parse the JSON data
        try:
            data = json.loads(json_data)
            messages = data.get("messages", [])
            
            # Get the last seen message
            last_seen = get_last_seen_message()
            
            # Check for new messages
            new_messages = []
            if last_seen:
                last_seen_id = last_seen.get("id")
                for message in messages:
                    if message.get("id") > last_seen_id:
                        new_messages.append(message)
            else:
                new_messages = messages
            
            # Process new messages
            for message in new_messages:
                logger.info(f"New message from {message.get('agent_id')}: {message.get('content')}")
            
            # Save the last message as the last seen
            if messages:
                save_last_seen_message(messages[-1])
        
        except Exception as e:
            logger.error(f"Error parsing JSON data: {e}")
    
    except Exception as e:
        logger.error(f"Error checking for new messages: {e}")

def main():
    """Main function."""
    logger.info("Starting monitor script...")
    
    while True:
        check_for_new_messages()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
