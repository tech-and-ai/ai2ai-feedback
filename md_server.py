#!/usr/bin/env python3
"""
Simple HTTP server with support for saving Markdown files
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime

# Port for the server
PORT = 8090

# Directory containing the HTML and Markdown files
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MarkdownChatHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the Markdown chat server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/save_markdown':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            filename = data.get('filename')
            content = data.get('content')
            
            # Validate the filename to prevent directory traversal
            if not filename or '..' in filename or '/' in filename:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Invalid filename')
                return
            
            # Save the file
            try:
                with open(os.path.join(DIRECTORY, filename), 'w') as f:
                    f.write(content)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'File saved successfully')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error saving file: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), MarkdownChatHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Markdown chat available at http://localhost:{PORT}/md_chat.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
