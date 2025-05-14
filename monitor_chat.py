#!/usr/bin/env python3
"""
Script to monitor the chat.md file for new messages and prompt Claude to respond
"""

import os
import time
import datetime
import hashlib

# Configuration
CHAT_FILE = "/home/admin/projects/ai2ai-feedback/chat.md"
CHECK_INTERVAL = 5  # seconds
LAST_HASH_FILE = "/home/admin/projects/ai2ai-feedback/.last_hash"

def get_file_hash():
    """Get the hash of the chat file."""
    if not os.path.exists(CHAT_FILE):
        return None
    
    with open(CHAT_FILE, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def get_last_hash():
    """Get the last known hash of the chat file."""
    if not os.path.exists(LAST_HASH_FILE):
        return None
    
    with open(LAST_HASH_FILE, "r") as f:
        return f.read().strip()

def save_last_hash(hash_value):
    """Save the hash of the chat file."""
    with open(LAST_HASH_FILE, "w") as f:
        f.write(hash_value)

def check_for_new_messages():
    """Check for new messages in the chat file."""
    current_hash = get_file_hash()
    last_hash = get_last_hash()
    
    if current_hash != last_hash:
        print(f"[{datetime.datetime.now()}] New message detected in chat.md!")
        print("Claude should respond by updating the chat.md file.")
        save_last_hash(current_hash)
        return True
    
    return False

def main():
    """Main function."""
    print(f"[{datetime.datetime.now()}] Starting chat monitor...")
    print(f"Monitoring {CHAT_FILE} for changes...")
    
    # Initialize the last hash
    current_hash = get_file_hash()
    if current_hash:
        save_last_hash(current_hash)
    
    while True:
        if check_for_new_messages():
            # This is where Claude would be prompted to respond
            pass
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
