import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Set environment variable for serverless
os.environ['VERCEL'] = '1'

from mangum import Mangum
from app.main import app

# Create Mangum adapter
_mangum_handler = Mangum(app, lifespan="off")

# Vercel expects a function named 'handler' for AWS Lambda-style invocation
def handler(event, context):
    return _mangum_handler(event, context)



