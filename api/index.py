from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Test endpoint
        if self.path == '/api' or self.path == '/api/':
            response = {
                "message": "Trading Bot API is running",
                "version": "1.0.0",
                "status": "ok"
            }
        else:
            response = {
                "path": self.path,
                "message": "API endpoint test"
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.do_GET()

