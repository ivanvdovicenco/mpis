"""
MPIS Genesis API - Health Check Router

Provides health and status endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.services.qdrant import QdrantService
from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with dependency status.
    
    Checks database and Qdrant connectivity.
    """
    status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "dependencies": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        status["dependencies"]["database"] = "healthy"
    except Exception as e:
        status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "degraded"
    
    # Check Qdrant
    try:
        qdrant = QdrantService()
        if qdrant.is_available():
            status["dependencies"]["qdrant"] = "healthy"
        else:
            status["dependencies"]["qdrant"] = "unavailable"
    except Exception as e:
        status["dependencies"]["qdrant"] = f"unhealthy: {str(e)}"
    
    return status


@router.get("/config")
async def get_config():
    """
    Get non-sensitive configuration values.
    
    Useful for debugging and client setup.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "dry_run": settings.DRY_RUN,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "chunk_min_tokens": settings.CHUNK_MIN_TOKENS,
        "chunk_max_tokens": settings.CHUNK_MAX_TOKENS,
        "public_web_max_sources": settings.PUBLIC_WEB_MAX_SOURCES,
        "qdrant_available": QdrantService().is_available()
    }
