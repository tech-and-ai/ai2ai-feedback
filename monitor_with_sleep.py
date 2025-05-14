#!/usr/bin/env python3
"""
Script to monitor the chat log with a sleep interval
"""

import os
import sys
import time
import datetime

# Configuration
LOG_FILE = "/home/admin/projects/ai2ai-feedback/chat.log"
SLEEP_INTERVAL = 10  # seconds

def get_last_message():
    """Get the last message from the log file."""
    if not os.path.exists(LOG_FILE):
        return None
    
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    
    if not lines:
        return None
    
    # Get the last line
    last_line = lines[-1].strip()
    
    # Parse the line
    try:
        # Format: [timestamp] sender: message
        parts = last_line.split("] ", 1)
        if len(parts) != 2:
            return None
        
        timestamp = parts[0][1:]  # Remove the leading [
        
        sender_message = parts[1].split(": ", 1)
        if len(sender_message) != 2:
            return None
        
        sender = sender_message[0]
        message = sender_message[1]
        
        return {
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        }
    except Exception as e:
        print(f"Error parsing last message: {e}", file=sys.stderr)
        return None

def add_response(message):
    """Add a response to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Claude: {message}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Added response: {message}")

def main():
    """Main function."""
    print(f"Monitoring {LOG_FILE} with {SLEEP_INTERVAL} second sleep interval...")
    print("Press Ctrl+C to exit")
    
    last_processed_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        while True:
            # Get the last message
            last_message = get_last_message()
            
            if last_message and last_message["sender"] != "Claude" and last_message["timestamp"] > last_processed_time:
                print(f"\nNew message from {last_message['sender']} at {last_message['timestamp']}:")
                print(f"  {last_message['message']}")
                
                # Update the last processed time
                last_processed_time = last_message["timestamp"]
                
                # Prompt for a response
                print("\nEnter your response (or press Enter to skip):")
                response = input("> ")
                
                if response:
                    add_response(response)
            
            # Sleep for the specified interval
            print(f"Sleeping for {SLEEP_INTERVAL} seconds...")
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    main()
