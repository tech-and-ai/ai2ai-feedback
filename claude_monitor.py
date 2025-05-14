#!/usr/bin/env python3
"""
Script for Claude to monitor the chat log and respond
"""

import os
import sys
import time
import datetime

# Configuration
LOG_FILE = "/home/admin/projects/ai2ai-feedback/chat.log"
CHECK_INTERVAL = 2  # seconds

def log_message(sender, message):
    """Log a message to the chat log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the log entry
    log_entry = f"[{timestamp}] {sender}: {message}\n"
    
    # Append to the log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Message logged: {log_entry.strip()}")

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

def main():
    """Main function."""
    print(f"Claude is now monitoring {LOG_FILE} for new messages...")
    
    # Initialize with a welcome message
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        log_message("Claude", "Hello! I'm Claude. I'm now monitoring this chat log and will respond to your messages. Type 'stop' to end the monitoring.")
    
    last_processed_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    while True:
        # Get the last message
        last_message = get_last_message()
        
        if last_message and last_message["sender"] != "Claude" and last_message["timestamp"] > last_processed_time:
            print(f"New message from {last_message['sender']}: {last_message['message']}")
            
            # Update the last processed time
            last_processed_time = last_message["timestamp"]
            
            # Check if the user wants to stop
            if last_message["message"].lower() == "stop":
                log_message("Claude", "Monitoring stopped as requested. Goodbye!")
                print("Monitoring stopped as requested.")
                break
            
            # Respond to the message
            response = f"I received your message: '{last_message['message']}'. This is an automated response from the monitoring script."
            log_message("Claude", response)
        
        # Wait before checking again
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
