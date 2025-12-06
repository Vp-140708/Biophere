# This file allows Render to run: uvicorn main:app
# It imports the FastAPI app from backend.main
from backend.main import app

__all__ = ["app"]
