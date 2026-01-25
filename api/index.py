import sys
import os

# Add backend directory to path so 'from app.config' works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from mangum import Mangum
from app.main import app

# Wrap FastAPI with Mangum for Vercel/AWS Lambda compatibility
handler = Mangum(app, lifespan="off")
