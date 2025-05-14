#!/usr/bin/env python3
"""
Simple HTTP server with support for updating files via PUT requests
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

# Port for the server
PORT = 8090

# Directory containing the HTML and Markdown files
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class AutoUpdateHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that supports PUT requests to update files."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_PUT(self):
        """Handle PUT requests to update files."""
        # Parse the path to get the filename
        parsed_path = urlparse(self.path)
        path = parsed_path.path.lstrip('/')
        
        # Validate the path to prevent directory traversal
        if '..' in path or path.startswith('/'):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid path')
            return
        
        # Get the full path to the file
        file_path = os.path.join(DIRECTORY, path)
        
        # Read the content length
        content_length = int(self.headers['Content-Length'])
        
        # Read the content
        content = self.rfile.read(content_length)
        
        try:
            # Write the content to the file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Send a success response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'File updated successfully')
            
            print(f"Updated file: {path}")
        except Exception as e:
            # Send an error response
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error updating file: {str(e)}'.encode())
            
            print(f"Error updating file {path}: {str(e)}", file=sys.stderr)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), AutoUpdateHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Chat viewer available at http://localhost:{PORT}/chat_viewer.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
