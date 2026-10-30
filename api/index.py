"""
PiBarX - Vercel Serverless Function Entrypoint
Directs incoming serverless requests to the FastAPI application
Normalizes paths rewritten by Vercel Edge rules
"""

import sys
from pathlib import Path

# Add project root directory to sys.path so 'backend' package resolves seamlessly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.main import app as fastapi_app


async def app(scope, receive, send):
    """ASGI proxy wrapper to normalize Vercel rewritten paths."""
    if scope.get("type") == "http":
        path = scope.get("path", "")
        if path.startswith("/api/index.py/"):
            scope["path"] = path[len("/api/index.py"):]
        elif path == "/api/index.py":
            scope["path"] = "/"
    await fastapi_app(scope, receive, send)
