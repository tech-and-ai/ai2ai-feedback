#!/usr/bin/env python3
"""
Simple HTTP server with support for logging chat messages
"""

import http.server
import socketserver
import os
import sys
import json
import urllib.parse
import datetime
from urllib.parse import parse_qs

# Port for the server
PORT = 8091

# Directory containing the HTML and log files
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(DIRECTORY, "chat.log")

# Create the log file if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("")

class LogHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the log server."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/log_message':
            # Get the content length
            content_length = int(self.headers['Content-Length'])

            # Read the POST data
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Parse the form data
            form_data = parse_qs(post_data)

            # Get the sender and message
            sender = form_data.get('sender', ['User'])[0]
            message = form_data.get('message', [''])[0]

            if not message:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Message cannot be empty')
                return

            try:
                # Log the message
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {sender}: {message}\n"

                with open(LOG_FILE, "a") as f:
                    f.write(log_entry)

                # Send a success response
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Message logged successfully')

                print(f"Logged message: {log_entry.strip()}")
            except Exception as e:
                # Send an error response
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error logging message: {str(e)}'.encode())

                print(f"Error logging message: {str(e)}", file=sys.stderr)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        # Special handling for the log file to ensure it's always up-to-date
        if self.path.startswith('/chat.log'):
            try:
                with open(LOG_FILE, 'rb') as f:
                    log_content = f.read()

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(log_content)
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error reading log file: {str(e)}'.encode())
                return

        # Handle other requests using the default handler
        return super().do_GET()

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), LogHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Log viewer available at http://localhost:{PORT}/log_viewer.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
