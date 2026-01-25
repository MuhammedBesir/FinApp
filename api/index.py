import sys
import os

# Add backend directory to path so 'from app.config' works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

# Vercel requires the app to be named 'app' or 'handler'
handler = app
