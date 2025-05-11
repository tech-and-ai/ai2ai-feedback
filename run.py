"""
Run script for AI-to-AI Feedback API

This script ensures a clean start of the server by:
1. Checking for and killing any existing processes on port 8001
2. Starting the application with proper error handling
"""

import os
import sys
import time
import signal
import socket
import subprocess
import logging
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("run-script")

# Load environment variables
load_dotenv()

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_on_port(port):
    """Find process ID using a specific port"""
    try:
        # Try using lsof
        cmd = f"lsof -i :{port} -t"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        if output:
            return [int(pid) for pid in output.split('\n')]
    except subprocess.CalledProcessError:
        pass

    try:
        # Try using netstat
        cmd = f"netstat -tulpn 2>/dev/null | grep :{port} | awk '{{print $7}}' | cut -d/ -f1"
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        if output:
            return [int(pid) for pid in output.split('\n')]
    except subprocess.CalledProcessError:
        pass

    return []

def kill_process(pid, force=False):
    """Kill a process by PID"""
    try:
        if force:
            os.kill(pid, signal.SIGKILL)
            logger.info(f"Forcefully killed process {pid}")
        else:
            os.kill(pid, signal.SIGTERM)
            logger.info(f"Terminated process {pid}")
        return True
    except ProcessLookupError:
        logger.warning(f"Process {pid} not found")
        return False
    except PermissionError:
        logger.warning(f"Permission denied to kill process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def kill_processes_on_port(port, force=False):
    """Kill all processes using a specific port"""
    if not is_port_in_use(port):
        logger.info(f"Port {port} is not in use")
        return True

    pids = find_process_on_port(port)
    if not pids:
        logger.warning(f"Port {port} is in use but couldn't find the process")
        return False

    success = True
    for pid in pids:
        if not kill_process(pid, force):
            success = False

    # Wait a moment and check if port is still in use
    time.sleep(1)
    if is_port_in_use(port):
        if not force:
            # Try again with force
            logger.info(f"Port {port} still in use, trying forceful kill")
            return kill_processes_on_port(port, force=True)
        else:
            logger.error(f"Failed to free port {port}")
            return False

    return success

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))

    # Ensure port is free
    if not kill_processes_on_port(port):
        logger.error(f"Failed to free port {port}, cannot start server")
        sys.exit(1)

    logger.info(f"Starting AI-to-AI Feedback API on {host}:{port}")
    try:
        uvicorn.run("app.main:app", host=host, port=port, reload=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)
