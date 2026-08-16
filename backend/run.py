"""
Entry-point for running the FastAPI backend.
Usage: python run.py
"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.APP_ENV == "development",
        log_level="info",
    )
