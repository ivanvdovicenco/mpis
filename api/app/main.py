"""
MPIS API - Main Application

FastAPI application for the Multi-Persona Intelligence System.
Includes Genesis, Life, Publisher, and Analytics modules.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db
from app.routers import (
    genesis_router, 
    health_router,
    life_router,
    publisher_router,
    analytics_router,
    dashboard_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"DRY_RUN mode: {settings.DRY_RUN}")
    
    yield
    
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
# MPIS - Multi-Persona Intelligence System API

A comprehensive API for creating, developing, and analyzing AI-powered digital personas.

## Modules

### Module 1: Persona Genesis Engine
Create personas from various sources through automated, human-supervised workflow.

### Module 2: Persona Life
Continuous persona evolution through real interactions, reflection cycles, and memory updates.

### Module 3: Social Publisher  
Plan, generate, approve, schedule, and publish content under persona voice.

### Module 4: Analytics Dashboard + EIDOS
Performance analytics and AI-powered actionable recommendations.

## Quick Start

1. **Create a persona**: `POST /genesis/start`
2. **Ingest life events**: `POST /life/event`
3. **Plan content**: `POST /publisher/plan`
4. **Generate content**: `POST /publisher/generate`
5. **Get recommendations**: `GET /analytics/recommendations/{persona_id}`
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(genesis_router)
app.include_router(life_router)
app.include_router(publisher_router)
app.include_router(analytics_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "modules": {
            "genesis": {
                "start": "POST /genesis/start",
                "status": "GET /genesis/status/{job_id}",
                "approve": "POST /genesis/approve"
            },
            "life": {
                "event": "POST /life/event",
                "cycle_start": "POST /life/cycle/start",
                "cycle_status": "GET /life/cycle/status/{cycle_id}",
                "cycle_approve": "POST /life/cycle/approve"
            },
            "publisher": {
                "plan": "POST /publisher/plan",
                "generate": "POST /publisher/generate",
                "draft": "GET /publisher/draft/{draft_id}",
                "approve": "POST /publisher/approve",
                "publish_record": "POST /publisher/publish/record",
                "metrics_ingest": "POST /publisher/metrics/ingest"
            },
            "analytics": {
                "summary": "GET /analytics/persona/{persona_id}/summary",
                "recompute": "POST /analytics/recompute",
                "recommendations": "GET /analytics/recommendations/{persona_id}"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
