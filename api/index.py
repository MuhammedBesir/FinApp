import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Set environment variable to skip heavy initializations in serverless
os.environ['VERCEL'] = '1'

from mangum import Mangum
from app.main import app

# Wrap FastAPI with Mangum for Vercel serverless
handler = Mangum(app, lifespan="off")


