# MPIS API - Routers Package
from app.routers.genesis import router as genesis_router
from app.routers.health import router as health_router
from app.routers.life import router as life_router
from app.routers.publisher import router as publisher_router
from app.routers.analytics import router as analytics_router

__all__ = [
    "genesis_router",
    "health_router",
    "life_router",
    "publisher_router",
    "analytics_router",
]
