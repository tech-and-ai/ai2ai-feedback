"""
Run script for starting the application with the simplified implementation.
"""
import os
import sys
import signal
import subprocess
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log")
    ]
)

logger = logging.getLogger(__name__)

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    try:
        # Find process ID using the port
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            # Get process IDs
            pids = result.stdout.strip().split("\n")
            
            # Kill each process
            for pid in pids:
                try:
                    pid = int(pid.strip())
                    os.kill(pid, signal.SIGTERM)
                    logger.info(f"Killed process {pid} on port {port}")
                except (ValueError, ProcessLookupError) as e:
                    logger.warning(f"Failed to kill process {pid}: {str(e)}")
            
            # Wait a moment for processes to terminate
            time.sleep(1)
            
            # Check if any processes are still running on the port
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                # Force kill any remaining processes
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        pid = int(pid.strip())
                        os.kill(pid, signal.SIGKILL)
                        logger.info(f"Force killed process {pid} on port {port}")
                    except (ValueError, ProcessLookupError) as e:
                        logger.warning(f"Failed to force kill process {pid}: {str(e)}")
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {str(e)}")

def main():
    """Main function to start the application."""
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", "8004"))
    
    # Kill any process running on the port
    logger.info(f"Checking for processes on port {port}")
    kill_process_on_port(port)
    
    # Start the application
    logger.info(f"Starting application on port {port}")
    
    # Use uvicorn to run the application
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
