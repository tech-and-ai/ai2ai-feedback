#!/usr/bin/env python3
"""
Worker Daemon

This script runs the worker as a background service that continuously
processes jobs from the queue.
"""
import os
import time
import logging
import signal
import sys
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("worker_daemon.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("worker_daemon")

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")

# Add the project root to the Python path
project_root = os.path.dirname(__file__)
sys.path.append(project_root)

# Import the WorkerDaemon class
from app.services.queue_engine.worker import WorkerDaemon

# Global flag for controlling the daemon
running = True

def signal_handler(sig, frame):
    """
    Handle signals for graceful shutdown.
    """
    global running
    logger.info(f"Received signal {sig}, shutting down")
    running = False

async def main():
    """
    Main function to run the worker daemon.
    """
    global running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize the worker daemon
        daemon = WorkerDaemon()
        
        # Start the daemon in a separate task
        daemon_task = asyncio.create_task(daemon.run())
        
        # Monitor the running flag
        while running:
            await asyncio.sleep(1)
        
        # Stop the daemon
        daemon.worker.stop()
        
        # Wait for the daemon to stop
        await daemon_task
        
    except Exception as e:
        logger.error(f"Error in worker daemon: {str(e)}")
    
    logger.info("Worker daemon exited")

if __name__ == "__main__":
    logger.info("Starting worker daemon")
    asyncio.run(main())
