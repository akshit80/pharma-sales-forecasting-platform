import sys
import os

# Add root directory to path for Vercel serverless imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app

# Vercel ASGI Handler entrypoint
handler = app
