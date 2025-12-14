# MPIS Genesis API - Routers Package
from app.routers.genesis import router as genesis_router
from app.routers.health import router as health_router

__all__ = [
    "genesis_router",
    "health_router",
]
