#!/usr/bin/env python3
"""
Run script for Lily AI.

This script starts the Lily AI application.
"""

import os
import sys
import signal
import subprocess
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_port(port):
    """Check if a port is in use."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def kill_process_on_port(port):
    """Kill the process using the specified port."""
    try:
        # Find process ID using the port
        output = subprocess.check_output(
            f"lsof -i :{port} -t", shell=True, stderr=subprocess.STDOUT
        ).decode().strip()
        
        if output:
            # Kill the process
            pid = int(output)
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Killed process {pid} using port {port}")
            return True
    except (subprocess.CalledProcessError, ValueError):
        pass
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {str(e)}")
    
    return False

def main():
    """Main function."""
    port = int(os.getenv("PORT", "8004"))
    
    # Check if port is in use
    if check_port(port):
        logger.warning(f"Port {port} is already in use")
        
        # Try to kill the process
        if kill_process_on_port(port):
            logger.info(f"Successfully freed port {port}")
        else:
            logger.error(f"Failed to free port {port}. Please close the application using this port.")
            sys.exit(1)
    
    # Start the application
    logger.info(f"Starting Lily AI on port {port}")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Lily AI")
    except Exception as e:
        logger.error(f"Error starting Lily AI: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
