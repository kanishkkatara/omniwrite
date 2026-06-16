"""
OmniWrite — FastAPI Application Entry Point
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.brand import router as brand_router
from backend.api.routes.generate import generate_router
from backend.api.routes.generate import router as jobs_router
from backend.api.routes.health import router as health_router
from backend.core.config import get_settings
from backend.services.storage import create_tables

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize database tables."""
    try:
        await create_tables()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield


app = FastAPI(
    title="OmniWrite API",
    description="Agentic multi-platform content generation API",
    version="0.1.0",
    lifespan=lifespan,
)

# Apply CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(brand_router, prefix="/api/v1")
app.include_router(generate_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
