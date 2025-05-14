#!/usr/bin/env python3
"""
Script to start the AI2AI Discussion API server
"""

import os
import sys
import subprocess
import time
import http.server
import socketserver
import threading
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = 8002
WEB_PORT = 8090
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP request handler with fixed directory."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_api_server():
    """Start the API server."""
    logger.info("Starting API server...")
    
    # Check if uvicorn is installed
    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn is not installed. Please install it with 'pip install uvicorn'.")
        sys.exit(1)
    
    # Check if FastAPI is installed
    try:
        import fastapi
    except ImportError:
        logger.error("fastapi is not installed. Please install it with 'pip install fastapi'.")
        sys.exit(1)
    
    # Check if aiohttp is installed
    try:
        import aiohttp
    except ImportError:
        logger.error("aiohttp is not installed. Please install it with 'pip install aiohttp'.")
        sys.exit(1)
    
    # Start the API server
    api_process = subprocess.Popen(
        [sys.executable, "discussion_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    logger.info(f"API server started on port {API_PORT}")
    
    return api_process

def start_web_server():
    """Start the web server."""
    logger.info("Starting web server...")
    
    # Start the web server
    with socketserver.TCPServer(("", WEB_PORT), SimpleHTTPRequestHandler) as httpd:
        logger.info(f"Web server started on port {WEB_PORT}")
        logger.info(f"Discussion UI available at http://localhost:{WEB_PORT}/ai2ai_discussion.html")
        httpd.serve_forever()

def main():
    """Main function."""
    # Start the API server
    api_process = start_api_server()
    
    # Wait for the API server to start
    logger.info("Waiting for API server to start...")
    time.sleep(2)
    
    # Start the web server in a separate thread
    web_thread = threading.Thread(target=start_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    try:
        # Monitor the API server process
        while True:
            line = api_process.stdout.readline()
            if not line:
                break
            print(line, end="")
    except KeyboardInterrupt:
        logger.info("Stopping servers...")
        api_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
