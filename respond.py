#!/usr/bin/env python3
"""
Simple script to add a response to the chat log
"""

import sys
import datetime

# Configuration
LOG_FILE = "/home/admin/projects/ai2ai-feedback/chat.log"

def add_response(message):
    """Add a response to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Claude: {message}\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
    
    print(f"Added response to chat.log")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python3 respond.py \"Your response message here\"")
        return
    
    # Get the message from command line arguments
    message = " ".join(sys.argv[1:])
    
    # Add the response to the log
    add_response(message)

if __name__ == "__main__":
    main()
