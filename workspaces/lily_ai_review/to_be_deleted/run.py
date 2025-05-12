#!/usr/bin/env python
"""
Run script for the Lily AI Research Pack Generator.

This script starts the application with proper initialization and environment handling.
It also starts the worker process in a separate thread.
"""
import os
import sys
import subprocess
import time
import signal
import logging
import threading
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger("run")

def kill_existing_process():
    """Kill any existing main.py and worker_launcher.py processes and free port 8004."""
    try:
        logger.info("Checking for existing application processes...")

        # First, kill any process using port 8004
        logger.info("Checking for processes using port 8004...")
        port_result = subprocess.run(
            "lsof -i :8004 | grep LISTEN | awk '{print $2}'",
            shell=True,
            capture_output=True,
            text=True
        )

        port_pids = port_result.stdout.strip().split('\n')
        port_pids = [pid for pid in port_pids if pid]

        if port_pids:
            logger.info(f"Found {len(port_pids)} processes using port 8004.")
            for pid in port_pids:
                try:
                    # First try SIGTERM for graceful shutdown
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Sent SIGTERM to process with PID {pid} using port 8004")
                except ProcessLookupError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to send SIGTERM to process {pid}: {str(e)}")

            # Give processes a moment to terminate gracefully
            time.sleep(1)

            # Check if any processes are still running and force kill them
            for pid in port_pids:
                try:
                    # Check if process still exists
                    os.kill(int(pid), 0)  # Signal 0 is used to check if process exists
                    logger.warning(f"Process {pid} still running after SIGTERM, sending SIGKILL")
                    # Process still exists, use SIGKILL
                    os.kill(int(pid), signal.SIGKILL)
                    logger.info(f"Forcefully terminated process with PID {pid}")
                except ProcessLookupError:
                    # Process no longer exists
                    logger.info(f"Process {pid} terminated successfully")
                except Exception as e:
                    logger.error(f"Failed to kill process {pid}: {str(e)}")

        # Then, find and kill any Python processes related to our application
        result = subprocess.run(
            "ps aux | grep 'python.*main.py\\|python.*worker_launcher.py\\|python.*run.py' | grep -v grep | awk '{print $2}'",
            shell=True,
            capture_output=True,
            text=True
        )

        pids = result.stdout.strip().split('\n')
        pids = [pid for pid in pids if pid and pid != str(os.getpid())]  # Exclude current process

        if pids:
            logger.info(f"Found {len(pids)} existing application processes.")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    logger.info(f"Sent SIGTERM to process with PID {pid}")
                except ProcessLookupError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to send SIGTERM to process {pid}: {str(e)}")

            # Give processes a moment to terminate gracefully
            time.sleep(1)

            # Check if any processes are still running and force kill them
            for pid in pids:
                try:
                    # Check if process still exists
                    os.kill(int(pid), 0)
                    logger.warning(f"Process {pid} still running after SIGTERM, sending SIGKILL")
                    # Process still exists, use SIGKILL
                    os.kill(int(pid), signal.SIGKILL)
                    logger.info(f"Forcefully terminated process with PID {pid}")
                except ProcessLookupError:
                    # Process no longer exists
                    logger.info(f"Process {pid} terminated successfully")
                except Exception as e:
                    logger.error(f"Failed to kill process {pid}: {str(e)}")

        # Give processes time to terminate and port to be released
        time.sleep(2)

        # Use a more aggressive approach to kill any remaining processes on port 8004
        subprocess.run(
            "fuser -k 8004/tcp",
            shell=True,
            capture_output=True,
            text=True
        )

        # Verify port 8004 is free
        verify_result = subprocess.run(
            "lsof -i :8004 | grep LISTEN",
            shell=True,
            capture_output=True,
            text=True
        )

        if verify_result.stdout.strip():
            logger.warning("Port 8004 is still in use after termination attempts. Trying one last forceful approach.")
            # One last attempt with fuser -k
            subprocess.run(
                "fuser -k -9 8004/tcp",
                shell=True,
                capture_output=True,
                text=True
            )
            time.sleep(1)

            # Final verification
            final_verify = subprocess.run(
                "lsof -i :8004 | grep LISTEN",
                shell=True,
                capture_output=True,
                text=True
            )

            if final_verify.stdout.strip():
                logger.error("Port 8004 is still in use. Application may fail to start.")
            else:
                logger.info("Port 8004 is now free after forceful termination.")
        else:
            logger.info("Port 8004 is now free.")

    except Exception as e:
        logger.error(f"Error while killing existing processes: {str(e)}")

# Global variable to track the worker process
worker_process = None

def run_worker():
    """Run the worker process."""
    global worker_process
    try:
        logger.info("Starting worker process...")
        # Execute the worker_launcher.py script
        worker_process = subprocess.Popen(
            [sys.executable, "worker_launcher.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # Log worker output
        for line in worker_process.stdout:
            logger.info(f"Worker: {line.strip()}")

        # If we get here, the worker has exited
        return_code = worker_process.wait()
        logger.info(f"Worker process exited with code {return_code}")
    except Exception as e:
        logger.error(f"Error running worker process: {str(e)}")

def check_environment():
    """Check and validate the environment variables."""
    load_dotenv()

    # Required variables
    required_vars = [
        ("SUPABASE_URL", "SUPABASE_PROJECT_URL"),
        ("SUPABASE_KEY", "SUPABASE_API_KEY"),
        ("STRIPE_API_KEY", None)
    ]

    missing_vars = []

    for primary, fallback in required_vars:
        if not os.getenv(primary) and (not fallback or not os.getenv(fallback)):
            missing_vars.append(primary if not fallback else f"{primary} or {fallback}")

    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Using default values for development. DO NOT use in production!")
    else:
        logger.info("All required environment variables are set.")

    # Set BASE_URL environment variable if not already set
    if not os.getenv("BASE_URL"):
        os.environ["BASE_URL"] = "https://researchassistant.uk"
        logger.info(f"Setting BASE_URL to {os.environ['BASE_URL']}")
    else:
        logger.info(f"Using BASE_URL: {os.getenv('BASE_URL')}")

def run_application():
    """Run the main application and worker process."""
    global worker_process

    # Start the worker process in a separate thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    logger.info("Worker thread started")

    try:
        logger.info("Starting Lily AI Research Pack Generator on port 8004...")

        # Set PORT environment variable to 8004
        os.environ["PORT"] = "8004"

        # Execute the main.py script
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Application exited with error code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        # Terminate the worker process if it's still running
        if worker_process and worker_process.poll() is None:
            logger.info("Terminating worker process...")
            worker_process.terminate()
            worker_process.wait(timeout=5)
            logger.info("Worker process terminated")
        return 0
    except Exception as e:
        logger.error(f"Error running application: {str(e)}")
        return 1
    finally:
        # Ensure the worker process is terminated when the main application exits
        if worker_process and worker_process.poll() is None:
            logger.info("Terminating worker process...")
            worker_process.terminate()
            try:
                worker_process.wait(timeout=5)
                logger.info("Worker process terminated")
            except subprocess.TimeoutExpired:
                logger.warning("Worker process did not terminate gracefully, killing it...")
                worker_process.kill()
                logger.info("Worker process killed")

if __name__ == "__main__":
    # Kill any existing processes
    kill_existing_process()

    # Check environment
    check_environment()

    # Run the application
    sys.exit(run_application())
