"""
Health check API routes.

GET /api/v1/health — Returns service health status, version, mode, and LLM availability.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    status: str
    version: str
    mode: str
    llm_available: bool
    research_enabled: bool


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    Returns the current health status of the service.

    Checks LLM key availability and returns configuration info.
    """
    from backend.core.config import get_settings

    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=_VERSION,
        mode=settings.default_mode,
        llm_available=settings.has_llm_key(),
        research_enabled=settings.research_enabled,
    )
