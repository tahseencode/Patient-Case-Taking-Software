"""Vercel Serverless Function entrypoint.

This module exposes the FastAPI ASGI `app` instance so Vercel can automatically
discover and execute it within the serverless Python runtime.
"""
import os
import sys

# Ensure project root is in sys.path so 'backend' package is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app  # noqa: E402, F401
