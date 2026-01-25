import sys
import os

# Add backend directory to path so 'from app.config' works
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

try:
    from mangum import Mangum
    from app.main import app
    
    # Wrap FastAPI with Mangum for Vercel/AWS Lambda compatibility
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Fallback: Create a simple debug handler if import fails
    from http.server import BaseHTTPRequestHandler
    import json
    import traceback
    
    error_msg = f"Import Error: {str(e)}\nTraceback: {traceback.format_exc()}"
    
    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Failed to initialize FastAPI app",
                "details": error_msg,
                "backend_path": backend_path,
                "sys_path": sys.path[:5]
            }).encode())
        
        def do_POST(self):
            self.do_GET()
