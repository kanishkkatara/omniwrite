"""
Content generation API routes.

Endpoints:
- POST /api/v1/generate                          — Create generation job
- GET  /api/v1/jobs/{job_id}                     — Get job status + outputs
- GET  /api/v1/jobs/{job_id}/stream              — SSE stream of AgentStep events
- POST /api/v1/jobs/{job_id}/approve-outline     — Submit outline approval/rejection
- POST /api/v1/jobs/{job_id}/regenerate/{platform} — Regenerate one platform
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.models.request import (
    ApproveOutlineRequest,
    GenerateRequest,
    Platform,
    RegenerateRequest,
)
from backend.services.job_service import job_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["generation"])
generate_router = APIRouter(tags=["generation"])


@generate_router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a content generation job",
)
async def create_generation_job(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Start a new content generation job.

    Returns immediately with a job_id. Use GET /jobs/{job_id} to poll status
    or GET /jobs/{job_id}/stream for real-time SSE updates.
    """
    from backend.services.brand_service import brand_service  # noqa: PLC0415

    # Resolve brand if brand_id provided
    brand = None
    if payload.brand_id:
        brand = await brand_service.get(payload.brand_id)
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand {payload.brand_id} not found",
            )

    job_id = await job_service.create_job(payload, brand_id=payload.brand_id)

    # Launch pipeline in background
    background_tasks.add_task(job_service.run_job, job_id, payload, brand)

    return {
        "job_id": str(job_id),
        "status": "pending",
        "message": "Job created. Stream updates at /api/v1/jobs/{job_id}/stream",
    }


@router.get(
    "/{job_id}",
    summary="Get job status and outputs",
)
async def get_job(job_id: UUID) -> dict:
    """
    Retrieve the current status and any available outputs for a job.

    Returns job metadata, step history, outputs, and cost summary.
    """
    job_data = await job_service.get_job(job_id)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job_data


@router.get(
    "/{job_id}/stream",
    summary="SSE stream of job progress events",
)
async def stream_job_events(job_id: UUID) -> EventSourceResponse:
    """
    Stream real-time Server-Sent Events for a generation job.

    Events:
    - `step`: An agent step completed (agent, status, message)
    - `outline_ready`: Outline generated and awaiting approval
    - `clarification_needed`: Brief needs more information
    - `done`: Job complete with outputs
    - `error`: Job failed
    - `ping`: Keep-alive heartbeat (every 30s)
    """
    # Verify job exists
    job_data = await job_service.get_job(job_id)
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    async def event_generator():
        async for event in job_service.stream_events(job_id):
            event_type = event.get("event", "message")
            data = event.get("data", {})
            yield {
                "event": event_type,
                "data": json.dumps(data),
            }

    return EventSourceResponse(event_generator())


@router.post(
    "/{job_id}/approve-outline",
    summary="Approve or reject the generated outline",
)
async def approve_outline(
    job_id: UUID,
    payload: ApproveOutlineRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Submit an outline approval decision.

    If approved=True, the pipeline resumes with writer agents.
    If approved=False, the job is cancelled.
    An optional edited_outline can be provided to use a modified version.
    """
    success = await job_service.approve_outline(
        job_id,
        approved=payload.approved,
        edited_outline=payload.edited_outline,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or not awaiting outline approval",
        )

    return {
        "job_id": str(job_id),
        "approved": payload.approved,
        "message": "Pipeline resuming…" if payload.approved else "Job cancelled",
    }


@router.post(
    "/{job_id}/regenerate/{platform}",
    summary="Regenerate content for a single platform",
)
async def regenerate_platform(
    job_id: UUID,
    platform: Platform,
    payload: RegenerateRequest | None = None,
    background_tasks: BackgroundTasks = None,
) -> dict:
    """
    Regenerate content for one platform with optional feedback instructions.

    The job must be in 'done' state. The updated output will be available
    via GET /jobs/{job_id} once complete.
    """
    feedback = payload.feedback if payload else None

    success = await job_service.regenerate_platform(
        job_id=job_id,
        platform=platform.value,
        feedback=feedback,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return {
        "job_id": str(job_id),
        "platform": platform.value,
        "status": "regenerating",
        "message": f"Regenerating {platform.value}. Poll GET /jobs/{job_id} for updates.",
    }
