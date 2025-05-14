#!/usr/bin/env python3
"""
Simple script to log chat messages to a file
"""

import os
import sys
import time
import datetime
import argparse

# Configuration
LOG_FILE = "/home/admin/projects/ai2ai-feedback/chat.log"

def log_message(sender, message):
    """Log a message to the chat log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the log entry
    log_entry = f"[{timestamp}] {sender}: {message}\n"
    
    # Append to the log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Message logged: {log_entry.strip()}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Log a chat message")
    parser.add_argument("--sender", "-s", default="User", help="Sender of the message")
    parser.add_argument("message", nargs="+", help="Message to log")
    
    args = parser.parse_args()
    
    # Join the message parts
    message = " ".join(args.message)
    
    # Log the message
    log_message(args.sender, message)

if __name__ == "__main__":
    main()
