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


from pydantic import BaseModel

from fastapi.responses import StreamingResponse

class ChatRequest(BaseModel):
    message: str
    active_platform: str


@router.post(
    "/{job_id}/chat",
    summary="Chat with generated content or request edits",
)
async def chat_with_content(
    job_id: UUID,
    payload: ChatRequest,
) -> StreamingResponse:
    """
    Handles conversational questions about the content or revision commands.
    Automatically classifies the message:
    - If user requests changes (e.g. rewrite, make it shorter, edit),
      initiates background platform regeneration and returns response_type="update".
    - If user asks a question, answers it directly and returns response_type="chat".
    """
    from backend.core.llm_factory import llm_call
    from backend.models.request import ModelMode
    from backend.services.storage import job_store
    import litellm
    from litellm import acompletion

    job = await job_store.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    import json
    request_data = json.loads(job.request_json) if job.request_json else {}
    topic = request_data.get("topic", "")
    outputs = json.loads(job.outputs_json) if job.outputs_json else {}
    state_data = json.loads(job.state_json) if job.state_json else {}
    outline = state_data.get("outline", "")

    classification_prompt = f"""You are analyzing a user's follow-up message in OmniWrite, an AI content generation tool.
The user is viewing a content generation project:
- Topic: {topic}
- Outline: {outline}
- Active Platform: {payload.active_platform}
- Generated Platform Content: {outputs.get(payload.active_platform, 'None')}

The user sent this message:
"{payload.message}"

Please determine if the user wants to UPDATE, REWRITE, REGENERATE, EDIT, or CHANGE the generated content (e.g., "rewrite the intro", "make it longer", "add a section about X", "change the title to funny").
Or if they are just asking a QUESTION, seeking explanation, commenting generally, or chatting (e.g., "what points did you cover?", "why did you choose this title?", "can you summarize the reddit post?", "looks good").

Output your analysis in this EXACT format:
[CLASSIFICATION] UPDATE
or
[CLASSIFICATION] CHAT
[ANSWER] Your helpful conversational answer to the user's message using the context above.
"""

    try:
        response_text, _, _, _ = await llm_call(
            messages=[{"role": "user", "content": classification_prompt}],
            agent_name=None,
            model_mode=ModelMode.TEST,
        )
    except Exception as e:
        logger.error(f"Chat LLM call failed: {e}")
        response_text = "[CLASSIFICATION] CHAT\n[ANSWER] I'm sorry, I was unable to process that chat request."

    lines = response_text.strip().split("\n")
    classification = "CHAT"
    content_answer = ""

    for line in lines:
        if line.startswith("[CLASSIFICATION]"):
            cls_val = line.replace("[CLASSIFICATION]", "").strip().upper()
            if cls_val in ("UPDATE", "CHAT"):
                classification = cls_val
        elif line.startswith("[ANSWER]"):
            content_answer = line.replace("[ANSWER]", "").strip()
            idx = response_text.find("[ANSWER]")
            if idx != -1:
                content_answer = response_text[idx + len("[ANSWER]"):].strip()
            break

    if not classification or (classification == "CHAT" and not content_answer):
        lower_resp = response_text.lower()
        if any(w in lower_resp for w in ["update", "rewrite", "regenerate", "make it", "change the"]):
            classification = "UPDATE"
        else:
            classification = "CHAT"
            content_answer = response_text.replace("[CLASSIFICATION]", "").replace("[ANSWER]", "").strip()

    if classification == "UPDATE":
        await job_service.regenerate_platform(
            job_id=job_id,
            platform=payload.active_platform,
            feedback=payload.message,
        )
        async def update_generator():
            yield json.dumps({"response_type": "update", "content": ""}) + "\n"
        return StreamingResponse(update_generator(), media_type="text/event-stream")
    else:
        async def chat_generator():
            chat_prompt = f"""You are an AI assistant for OmniWrite. Answer the user's question.
Topic: {topic}
Outline: {outline}
Active Platform: {payload.active_platform}
Generated Content: {outputs.get(payload.active_platform, 'None')}

User Question: {payload.message}
Answer helpfully and concisely.
"""
            from backend.core.config import get_settings
            from backend.core.llm_factory import _inject_api_keys
            settings = get_settings()
            _inject_api_keys(settings)
            model_cfg = settings.get_model_config(None)

            kwargs = {
                "model": model_cfg.model,
                "messages": [{"role": "user", "content": chat_prompt}],
                "temperature": model_cfg.temperature,
                "max_tokens": model_cfg.max_tokens,
                "timeout": model_cfg.timeout,
                "stream": True,
            }
            if model_cfg.base_url:
                kwargs["base_url"] = model_cfg.base_url

            try:
                # Signal CHAT response start
                yield json.dumps({"response_type": "chat", "content": ""}) + "\n"

                response = await acompletion(**kwargs)
                async for chunk in response:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield json.dumps({"response_type": "chat", "content": delta}) + "\n"
            except Exception as e:
                logger.error(f"Streaming LLM call failed: {e}")
                yield json.dumps({"response_type": "chat", "content": "\n[Error occurred during streaming]"}) + "\n"

        return StreamingResponse(chat_generator(), media_type="text/event-stream")
