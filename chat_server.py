#!/usr/bin/env python3
"""
Simple HTTP server with support for updating the chat.md file
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
CHAT_FILE = os.path.join(DIRECTORY, "chat.md")

class ChatHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the chat server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/update_chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            message = data.get('message', '').strip()
            
            if not message:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Message cannot be empty')
                return
            
            try:
                # Get the current content of the chat file
                with open(CHAT_FILE, 'r') as f:
                    content = f.read()
                
                # Add the user's message with timestamp
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                
                # Format the message to add
                user_message = f"\n\n## User ({timestamp})\n{message}"
                
                # Append the message to the markdown
                content += user_message
                
                # Write the updated content back to the file
                with open(CHAT_FILE, 'w') as f:
                    f.write(content)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Message added successfully')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error updating chat file: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Chat viewer available at http://localhost:{PORT}/chat_viewer.html")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
