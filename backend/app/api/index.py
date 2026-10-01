import os
import sys

# Make the project root importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # Vercel looks for a variable named `app`