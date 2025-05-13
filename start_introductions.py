#!/usr/bin/env python3
"""
Script to start introductions between AI agents using the AI2AI feedback system
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
import aiohttp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = "http://localhost:8002"  # The AI2AI feedback API server

async def create_discussion():
    """Create a new discussion."""
    url = f"{API_URL}/discussion/create"
    
    # Discussion configuration
    data = {
        "title": "AI Agent Introductions",
        "agents": [
            {
                "name": "DeepSeek Coder",
                "role": "Code Expert",
                "model": "deepseek-coder-v2:16b"
            },
            {
                "name": "Gemma 3 4B",
                "role": "General Assistant",
                "model": "gemma3:4b"
            }
        ],
        "system_prompt": "You are AI agents participating in a collaborative discussion. Introduce yourselves, your capabilities, and how you can work together to solve problems."
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Created discussion: {result}")
                    return result.get("session_id")
                else:
                    error_text = await response.text()
                    logger.error(f"Error creating discussion: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Exception creating discussion: {e}")
        return None

async def send_message(session_id, content, sender="chair"):
    """Send a message to the discussion."""
    url = f"{API_URL}/discussion/message"
    
    data = {
        "session_id": session_id,
        "content": content,
        "sender": sender
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Sent message: {result}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Error sending message: {error_text}")
                    return False
    except Exception as e:
        logger.error(f"Exception sending message: {e}")
        return False

async def main():
    """Main function."""
    # Create a new discussion
    session_id = await create_discussion()
    
    if not session_id:
        logger.error("Failed to create discussion")
        return
    
    logger.info(f"Created discussion with session ID: {session_id}")
    
    # Send initial message to start introductions
    initial_message = "Welcome to this collaborative discussion. Please introduce yourselves, your capabilities, and how you can work together to solve problems."
    
    success = await send_message(session_id, initial_message)
    
    if success:
        logger.info("Successfully started introductions")
        logger.info(f"You can view the discussion at: http://localhost:8002/discussion/stream/{session_id}")
    else:
        logger.error("Failed to send initial message")

if __name__ == "__main__":
    asyncio.run(main())
