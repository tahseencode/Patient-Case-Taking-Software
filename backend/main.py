"""Vercel entrypoint.

Vercel looks for a FastAPI `app` in a root-level main.py. The real application
lives in backend/main.py and uses `backend.app...` imports, which only resolve
when the repository root is on sys.path - so we import it from here.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.main import app  # noqa: E402,F401
