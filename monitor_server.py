#!/usr/bin/env python3
"""
Simple HTTP server for the AI2AI Discussion Monitor
"""

import http.server
import socketserver
import os
import json
import urllib.parse
from datetime import datetime
import threading
import time

# Sample discussion data
DISCUSSION_DATA = {
    "messages": [
        {
            "id": "1",
            "agent_id": "human",
            "content": "I have a recursive Fibonacci function in Python that's very slow for large inputs. How can I optimize it?",
            "timestamp": "2023-05-13T23:27:02.812Z"
        },
        {
            "id": "2",
            "agent_id": "agent1",
            "content": """Optimizing a recursive Fibonacci function can be done in several ways:

1. **Memoization (Caching)**: Store previously computed values to avoid redundant calculations.
```python
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
```

2. **Dynamic Programming (Iterative Approach)**: Avoid recursion altogether.
```python
def fibonacci(n):
    if n <= 1:
        return n
    fib = [0] * (n+1)
    fib[1] = 1
    for i in range(2, n+1):
        fib[i] = fib[i-1] + fib[i-2]
    return fib[n]
```

3. **Matrix Exponentiation**: For very large values, use matrix multiplication.
```python
import numpy as np

def fibonacci(n):
    F = np.array([[1, 1], [1, 0]], dtype=np.int64)
    if n == 0:
        return 0
    return matrix_power(F, n-1)[0, 0]
    
def matrix_power(M, power):
    if power <= 0:
        return np.identity(M.shape[0], dtype=M.dtype)
    if power % 2 == 0:
        return matrix_power(np.dot(M, M), power // 2)
    return np.dot(M, matrix_power(M, power-1))
```

The memoization approach is simplest and very effective for most cases.""",
            "timestamp": "2023-05-13T23:27:15.123Z"
        },
        {
            "id": "3",
            "agent_id": "human",
            "content": "Can you provide a specific implementation using memoization?",
            "timestamp": "2023-05-13T23:27:28.545Z"
        },
        {
            "id": "4",
            "agent_id": "agent1",
            "content": """Here's a specific implementation of the Fibonacci function using memoization:

```python
def fibonacci(n, memo={}):
    # Base case
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
        
    # Calculate and store result
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
```

You can use it like this:

```python
# Test with different values
print(fibonacci(10))  # 55
print(fibonacci(30))  # 832040
print(fibonacci(100)) # 354224848179261915075
```

Note: There's a potential issue with using a mutable default argument (the memo dictionary). For production code, you might want to use this version instead:

```python
def fibonacci(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
```

This implementation has O(n) time complexity instead of the O(2^n) of the naive recursive approach.""",
            "timestamp": "2023-05-13T23:27:37.630Z"
        }
    ]
}

# Port for the server
PORT = 8080

# Directory containing the HTML file
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DiscussionMonitorHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for the discussion monitor server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            # Redirect to the monitor page
            self.send_response(301)
            self.send_header('Location', '/discussion_monitor.html')
            self.end_headers()
            return
        elif self.path == '/api/discussion':
            # Return the discussion data as JSON
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(DISCUSSION_DATA).encode())
            return
        
        # Handle other requests using the default handler
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/message':
            # Get the message data from the request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            message_data = json.loads(post_data)
            
            # Add the message to the discussion
            new_message = {
                "id": str(len(DISCUSSION_DATA["messages"]) + 1),
                "agent_id": message_data.get("agent_id", "human"),
                "content": message_data.get("content", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            DISCUSSION_DATA["messages"].append(new_message)
            
            # Return success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": new_message}).encode())
            return
        
        # Handle other POST requests
        self.send_response(404)
        self.end_headers()

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), DiscussionMonitorHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Discussion monitor available at http://localhost:{PORT}/discussion_monitor.html")
        httpd.serve_forever()

if __name__ == "__main__":
    # Start the server
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.")
