#!/usr/bin/env python
"""
Run script for Lily AI Research Pack Generator.

This script:
1. Checks if the application is already running on the specified port
2. Kills any existing processes on that port
3. Starts the application
"""
import os
import sys
import signal
import socket
import logging
import subprocess
import time
try:
    from dotenv import load_dotenv
except ImportError:
    # Define a simple load_dotenv function if python-dotenv is not installed
    def load_dotenv():
        """Simple dotenv loader that does nothing."""
        logger.warning("python-dotenv not installed, using environment variables as is.")
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("run.log")
    ]
)

logger = logging.getLogger("run")

# Load environment variables
load_dotenv()

def is_port_in_use(port):
    """
    Check if a port is in use.

    Args:
        port: The port to check

    Returns:
        bool: True if the port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """
    Kill any process running on the specified port.

    Args:
        port: The port to kill processes on

    Returns:
        bool: True if a process was killed, False otherwise
    """
    try:
        # Use a more forceful approach with fuser
        subprocess.run(
            f"fuser -k {port}/tcp",
            shell=True,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE
        )
        logger.info(f"Killed processes on port {port}")
        return True

    except subprocess.CalledProcessError:
        # No process found on the port
        return False

    except Exception as e:
        logger.error(f"Error killing process on port {port}: {str(e)}")
        return False

def main():
    """
    Main function to run the application.
    """
    # Get port from environment variables
    port = int(os.getenv("PORT", 8004))

    # Check if the port is in use
    if is_port_in_use(port):
        logger.info(f"Port {port} is in use. Attempting to kill the process...")

        # Kill the process
        if kill_process_on_port(port):
            # Wait for the port to be released
            time.sleep(1)
        else:
            logger.warning(f"Failed to kill process on port {port}")

    # Start the application
    try:
        logger.info(f"Starting application on port {port}...")

        # Run the application
        subprocess.run(
            [sys.executable, "main.py"],
            check=True
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"Application exited with error code {e.returncode}")
        sys.exit(e.returncode)

    except Exception as e:
        logger.error(f"Error running application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
