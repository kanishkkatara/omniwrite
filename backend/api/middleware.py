"""
FastAPI middleware for omniwrite.

Provides:
- CORS middleware with configurable origins
- Request ID injection (X-Request-ID header)
- Basic in-memory rate limiting (10 req/min per IP)
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

if TYPE_CHECKING:
    from fastapi import FastAPI


# ── Rate limiter state ────────────────────────────────────────────────────────

_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 60       # requests
_RATE_WINDOW = 60.0    # seconds


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID header into every request and response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple token-bucket rate limiter keyed by client IP.

    Allows _RATE_LIMIT requests per _RATE_WINDOW seconds.
    Returns 429 Too Many Requests when exceeded.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks and metrics
        if request.url.path in ("/api/v1/health", "/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Prune old timestamps
        _rate_store[client_ip] = [
            ts for ts in _rate_store[client_ip] if now - ts < _RATE_WINDOW
        ]

        if len(_rate_store[client_ip]) >= _RATE_LIMIT:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again in a minute."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        _rate_store[client_ip].append(now)
        return await call_next(request)


def setup_middleware(app: "FastAPI") -> None:
    """
    Register all middleware on the FastAPI app.

    Call this once during app construction.
    """
    from backend.core.config import get_settings

    settings = get_settings()

    # CORS — must be added first (outermost layer)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # Request ID
    app.add_middleware(RequestIDMiddleware)
