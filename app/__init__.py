"""Valuation Agent Backend API."""

# Import the main FastAPI app from the parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app from the parent directory's app.py
import importlib.util
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = app_module.app

__all__ = ["app"]