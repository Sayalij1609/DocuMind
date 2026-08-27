from fastapi import FastAPI
from app.core.config import settings
from app.api.document_routes import router as document_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Nexora - Intelligent Document Processing "
        "and Understanding System"
    )
)

app.include_router(document_router)
@app.get("/")
async def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }