import sys
import os

# Add backend directory to path so 'from app.config' works
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
