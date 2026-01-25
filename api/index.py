import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Set environment variable for serverless
os.environ['VERCEL'] = '1'

# Import FastAPI app - Vercel should auto-detect ASGI
from app.main import app




