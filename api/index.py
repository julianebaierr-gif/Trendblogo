import sys
import os
from pathlib import Path

# Add the project root to sys.path so that 'app' module can be found
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Explicitly set Vercel environment flag
os.environ["VERCEL"] = "1"

# Import the FastAPI application instance
from app.main import app
