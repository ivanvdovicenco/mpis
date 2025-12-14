"""
MPIS Genesis API - Main Application

FastAPI application for the Persona Genesis Engine.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db
from app.routers import genesis_router, health_router

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
# MPIS Genesis API

The Persona Genesis Engine is Module 1 of the Multi-Persona Intelligence System (MPIS).

## Features

- **Source Collection**: Collect from YouTube, Google Drive, and web sources
- **Corpus Processing**: Normalize, chunk, and embed source materials
- **Concept Extraction**: Extract themes, virtues, tone, and key ideas
- **Persona Generation**: Generate complete persona_core.json with LLM
- **Human Approval Loop**: Review, edit, and approve persona drafts
- **Export**: Generate complete persona folder structure

## Workflow

1. **Start**: `POST /genesis/start` - Begin generation with sources
2. **Review**: `GET /genesis/status/{job_id}` - Check progress
3. **Approve**: `POST /genesis/approve` - Confirm or edit draft
4. **Export**: `GET /genesis/export/{persona_id}` - Get export paths

## Source Channels

- **Channel A**: YouTube links from `youtube_links.txt`
- **Channel B**: Google Drive folder (PDF/DOCX/Google Docs)
- **Channel C**: Public persona web enrichment (SerpAPI/Wikipedia)
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "genesis": {
            "start": "POST /genesis/start",
            "status": "GET /genesis/status/{job_id}",
            "approve": "POST /genesis/approve"
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
