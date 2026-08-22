from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Document Intelligence Platform",
    version=settings.APP_VERSION
)


@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "message": "Intelligent Document Intelligence Platform",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }