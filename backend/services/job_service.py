"""
Job Service.

Manages the lifecycle of content generation jobs:
- Creates job records
- Executes the LangGraph pipeline
- Streams progress events via asyncio.Queue (for SSE)
- Stores intermediate and final state in the database
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from backend.models.request import GenerateRequest
from backend.models.state import AgentState
from backend.services.storage import job_store

logger = logging.getLogger(__name__)

# In-memory SSE event queues: job_id → asyncio.Queue of event dicts
_event_queues: dict[str, asyncio.Queue] = {}

# In-memory state snapshots for outline approval resume
_pending_states: dict[str, dict[str, Any]] = {}


class JobService:
    """Manages content generation jobs and SSE streaming."""

    # ── Job management ────────────────────────────────────────────────────────

    async def create_job(self, request: GenerateRequest, brand_id: UUID | None = None) -> UUID:
        """
        Create a new job record and return its ID.

        Args:
            request: The generation request.
            brand_id: Optional brand ID to attach.

        Returns:
            The new job's UUID.
        """
        request_data = request.model_dump(mode="json")
        job = await job_store.create_job(request_data, brand_id=brand_id)
        return job.id

    async def get_job(self, job_id: UUID) -> dict[str, Any] | None:
        """
        Fetch current job state as a dict.

        Returns:
            Dict with keys: id, status, outputs, outline, error, steps, cost
        """
        job = await job_store.get_job(job_id)
        if not job:
            return None

        outputs: dict = {}
        state_data: dict = {}
        try:
            outputs = json.loads(job.outputs_json) if job.outputs_json else {}
        except json.JSONDecodeError:
            pass
        try:
            state_data = json.loads(job.state_json) if job.state_json else {}
        except json.JSONDecodeError:
            pass

        # Map internal DB status strings to API status strings expected by frontend
        status = job.status
        if status in ("done", "completed"):
            status = "completed"
        elif status in ("error", "failed"):
            status = "failed"

        return {
            "id": str(job.id),
            "status": status,
            "outputs": outputs,
            "outline": state_data.get("outline", ""),
            "steps": state_data.get("steps", []),
            "error": job.error,
            "total_cost_usd": state_data.get("total_cost_usd", 0.0),
            "total_input_tokens": state_data.get("total_input_tokens", 0),
            "total_output_tokens": state_data.get("total_output_tokens", 0),
            "created_at": job.created_at.isoformat(),
        }

    # ── Pipeline execution ────────────────────────────────────────────────────

    async def run_job(
        self,
        job_id: UUID,
        request: GenerateRequest,
        brand: Any | None = None,
    ) -> None:
        """
        Execute the LangGraph pipeline for a job.

        Runs in the background (called from the route handler via asyncio.create_task).
        Streams step events to the SSE queue and persists final state.

        Args:
            job_id: The job UUID.
            request: The generation request.
            brand: Optional BrandProfile.
        """
        from backend.agents.graph import create_graph  # noqa: PLC0415
        from backend.core.config import get_settings  # noqa: PLC0415

        settings = get_settings()
        if request.test_model or request.production_model:
            settings = settings.model_copy()
            settings.models = dict(settings.models)
            if request.test_model:
                settings.models["test"] = settings.models["test"].model_copy(
                    update={"model": request.test_model}
                )
            if request.production_model:
                settings.models["production"] = settings.models["production"].model_copy(
                    update={"model": request.production_model}
                )
        job_id_str = str(job_id)

        # Initialise SSE queue
        queue: asyncio.Queue = asyncio.Queue()
        _event_queues[job_id_str] = queue

        await job_store.update_job_status(job_id, "running")

        initial_state = AgentState(
            job_id=job_id,
            request=request,
            brand=brand,
            start_time=time.time(),
        )

        async def _emit(event_type: str, data: dict) -> None:
            await queue.put({"event": event_type, "data": data})

        await _emit("status", {"status": "running", "step": "starting"})

        try:
            graph = create_graph(settings)
            state_dict = initial_state.model_dump(mode="json")

            final_state_dict: dict[str, Any] = {}

            # Stream graph events
            async for event in graph.astream(state_dict):
                # event is a dict like {"node_name": state_dict}
                for node_name, node_state in event.items():
                    if not isinstance(node_state, dict):
                        continue
                    final_state_dict = node_state

                    # Emit step update
                    steps = node_state.get("steps", [])
                    if steps:
                        last_step = steps[-1]
                        await _emit(
                            "step",
                            {
                                "agent": last_step.get("agent", node_name),
                                "status": last_step.get("status", "running"),
                                "message": last_step.get("message", ""),
                            },
                        )

                    # Check if waiting for outline approval
                    if not node_state.get("outline_approved", True) and node_state.get("outline"):
                        await _emit(
                            "outline_ready",
                            {
                                "outline": node_state["outline"],
                                "message": "Outline ready for review",
                            },
                        )
                        # Save state for resume
                        _pending_states[job_id_str] = node_state
                        await job_store.update_job_status(job_id, "awaiting_outline_approval")
                        await job_store.update_job_state(job_id, node_state)
                        await queue.put(None)  # Signal stream end
                        return

                    # Check if waiting for brief clarification
                    brief_data = node_state.get("brief") or {}
                    if isinstance(brief_data, dict) and not brief_data.get("is_complete", True):
                        questions = brief_data.get("clarifying_questions", [])
                        await _emit(
                            "clarification_needed",
                            {
                                "questions": questions,
                            },
                        )
                        await job_store.update_job_status(job_id, "awaiting_clarification")
                        await job_store.update_job_state(job_id, node_state)
                        await queue.put(None)
                        return

                    # Persist intermediate state
                    await job_store.update_job_state(job_id, node_state)

            # Pipeline complete
            if final_state_dict:
                end_time = time.time()
                final_state_dict["end_time"] = end_time

                outputs_json: dict = {}
                for k, v in (final_state_dict.get("outputs") or {}).items():
                    if isinstance(v, dict):
                        outputs_json[k] = v

                await job_store.update_job_outputs(job_id, outputs_json, final_state_dict)
                await job_store.update_job_status(job_id, "done")

                await _emit(
                    "done",
                    {
                        "status": "done",
                        "outputs": outputs_json,
                        "total_cost_usd": final_state_dict.get("total_cost_usd", 0.0),
                    },
                )
            else:
                await job_store.update_job_status(job_id, "done")
                await _emit("done", {"status": "done"})

        except Exception as exc:  # noqa: BLE001
            logger.exception("Job %s failed: %s", job_id, exc)
            await job_store.update_job_status(job_id, "error", error=str(exc))
            await _emit("error", {"error": str(exc), "message": str(exc)})

        finally:
            await queue.put(None)  # Signal stream end

    # ── Outline approval ──────────────────────────────────────────────────────

    async def approve_outline(
        self,
        job_id: UUID,
        approved: bool,
        edited_outline: str | None = None,
    ) -> bool:
        """
        Resume the pipeline after outline approval.

        Args:
            job_id: The job UUID.
            approved: Whether the outline was approved.
            edited_outline: Optional user-edited outline text.

        Returns:
            True if resumption was triggered, False if job not found/not waiting.
        """
        job_id_str = str(job_id)

        if not approved:
            await job_store.update_job_status(job_id, "cancelled")
            return True

        pending_state = _pending_states.pop(job_id_str, None)
        if not pending_state:
            # Try to load from DB
            job = await job_store.get_job(job_id)
            if not job or job.status != "awaiting_outline_approval":
                return False
            try:
                pending_state = json.loads(job.state_json)
            except Exception:
                return False

        # Apply edited outline if provided
        pending_state["outline_approved"] = True
        if edited_outline:
            pending_state["outline_edited"] = edited_outline
            pending_state["outline"] = edited_outline

        # Resume the pipeline
        job = await job_store.get_job(job_id)
        if not job:
            return False

        request_data = json.loads(job.request_json)
        from backend.models.request import GenerateRequest  # noqa: PLC0415

        request = GenerateRequest(**request_data)

        # Reconstruct state and run writers + editor
        from backend.core.config import get_settings  # noqa: PLC0415

        settings = get_settings()

        async def _resume():
            queue = _event_queues.get(job_id_str) or asyncio.Queue()
            _event_queues[job_id_str] = queue

            await job_store.update_job_status(job_id, "running")
            try:
                # Run writers and editor from the pending state
                from backend.models.state import AgentState  # noqa: PLC0415

                state = AgentState(**pending_state)

                from backend.agents.blog_writer import write_blog  # noqa: PLC0415
                from backend.agents.editor_agent import run_editor  # noqa: PLC0415
                from backend.agents.linkedin_commenter import (
                    write_linkedin_comment,  # noqa: PLC0415
                )
                from backend.agents.linkedin_writer import write_linkedin  # noqa: PLC0415
                from backend.agents.reddit_writer import write_reddit  # noqa: PLC0415

                platforms_to_write: set[str] = set()
                if request.platforms:
                    platforms_to_write = {p.value for p in request.platforms}
                else:
                    platforms_to_write = {"blog", "linkedin", "reddit"}

                if "blog" in platforms_to_write:
                    state = await write_blog(state, settings)
                if "reddit" in platforms_to_write:
                    state = await write_reddit(state, settings)
                if "linkedin" in platforms_to_write:
                    state = await write_linkedin(state, settings)
                if "linkedin_comment" in platforms_to_write:
                    state = await write_linkedin_comment(state, settings)

                state = await run_editor(state, settings)

                outputs_json = {k: v.model_dump(mode="json") for k, v in state.outputs.items()}
                state_dict = state.model_dump(mode="json")
                state_dict["end_time"] = time.time()

                await job_store.update_job_outputs(job_id, outputs_json, state_dict)
                await job_store.update_job_status(job_id, "done")
                await queue.put(
                    {"event": "done", "data": {"status": "done", "outputs": outputs_json}}
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Resume after outline approval failed: %s", exc)
                await job_store.update_job_status(job_id, "error", error=str(exc))
                await queue.put(
                    {"event": "error", "data": {"error": str(exc), "message": str(exc)}}
                )
            finally:
                await queue.put(None)

        asyncio.create_task(_resume())
        return True

    # ── SSE streaming ─────────────────────────────────────────────────────────

    async def stream_events(self, job_id: UUID) -> AsyncGenerator[dict, None]:
        """
        Async generator of SSE events for a job.

        Yields event dicts until the job is complete (None sentinel received).
        Falls back to polling from DB if no live queue is available.

        Args:
            job_id: The job UUID.

        Yields:
            Event dicts with "event" and "data" keys.
        """
        job_id_str = str(job_id)
        queue = _event_queues.get(job_id_str)

        if queue is None:
            # Job is already done — check DB and emit final event to close client stream
            job_data = await self.get_job(job_id)
            if job_data:
                status = job_data.get("status")
                if status == "completed":
                    yield {
                        "event": "job_complete",
                        "data": {"cost": {"total_cost": job_data.get("total_cost_usd", 0.0)}},
                    }
                elif status == "failed":
                    yield {
                        "event": "error",
                        "data": {"message": job_data.get("error") or "Job failed"},
                    }
                else:
                    yield {"event": "status", "data": job_data}
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                if event is None:
                    break
                yield event
                queue.task_done()
            except TimeoutError:
                yield {"event": "ping", "data": {"alive": True}}

        # Cleanup
        _event_queues.pop(job_id_str, None)

    # ── Regenerate one platform ───────────────────────────────────────────────

    async def regenerate_platform(
        self,
        job_id: UUID,
        platform: str,
        feedback: str | None = None,
    ) -> bool:
        """
        Regenerate content for a single platform.

        Args:
            job_id: The job UUID.
            platform: Platform name (e.g. "blog", "linkedin").
            feedback: Optional regeneration instructions.

        Returns:
            True if regeneration was triggered, False otherwise.
        """
        job = await job_store.get_job(job_id)
        if not job:
            return False

        try:
            state_data = json.loads(job.state_json or "{}")
            request_data = json.loads(job.request_json or "{}")
        except json.JSONDecodeError:
            return False

        from backend.core.config import get_settings  # noqa: PLC0415
        from backend.models.request import GenerateRequest  # noqa: PLC0415
        from backend.models.state import AgentState  # noqa: PLC0415

        settings = get_settings()
        request = GenerateRequest(**request_data)
        if request.test_model or request.production_model:
            settings = settings.model_copy()
            settings.models = dict(settings.models)
            if request.test_model:
                settings.models["test"] = settings.models["test"].model_copy(
                    update={"model": request.test_model}
                )
            if request.production_model:
                settings.models["production"] = settings.models["production"].model_copy(
                    update={"model": request.production_model}
                )

        job_id_str = str(job_id)
        queue: asyncio.Queue = asyncio.Queue()
        _event_queues[job_id_str] = queue

        await job_store.update_job_status(job_id, "running")

        async def _regen():
            try:
                # Emit initial regeneration step
                await queue.put(
                    {
                        "event": "step_update",
                        "data": {
                            "id": f"regen_{platform}",
                            "name": f"regen_{platform}",
                            "status": "running",
                            "message": f"Initiating regeneration for {platform}…",
                        },
                    }
                )

                # Update DB state with running step
                state = AgentState(**state_data)
                state.add_step(
                    f"regen_{platform}", "running", f"Initiating regeneration for {platform}…"
                )
                await job_store.update_job_state(job_id, state.model_dump(mode="json"))

                if feedback:
                    # Inject feedback as additional context
                    if state.brief:
                        state.brief.key_points.append(f"Feedback for regeneration: {feedback}")

                # Remove old output so plugin regenerates fresh
                state.outputs.pop(platform, None)

                plugin_map = {
                    "blog": ("backend.agents.blog_writer", "write_blog"),
                    "reddit": ("backend.agents.reddit_writer", "write_reddit"),
                    "linkedin": ("backend.agents.linkedin_writer", "write_linkedin"),
                    "linkedin_comment": (
                        "backend.agents.linkedin_commenter",
                        "write_linkedin_comment",
                    ),
                }

                if platform not in plugin_map:
                    return

                import importlib  # noqa: PLC0415

                mod_path, fn_name = plugin_map[platform]
                mod = importlib.import_module(mod_path)
                fn = getattr(mod, fn_name)

                # Emit active writing step
                await queue.put(
                    {
                        "event": "step_update",
                        "data": {
                            "id": f"{platform}_writer",
                            "name": f"{platform}_writer",
                            "status": "running",
                            "message": f"Running writer agent for {platform}…",
                        },
                    }
                )
                state.add_step(
                    f"{platform}_writer", "running", f"Running writer agent for {platform}…"
                )
                await job_store.update_job_state(job_id, state.model_dump(mode="json"))

                # Execute writer
                state = await fn(state, settings)

                # Update completed steps in state
                for s in state.steps:
                    if s.agent == f"regen_{platform}":
                        s.status = "done"
                        s.message = f"Regeneration for {platform} completed successfully."
                    elif s.agent == f"{platform}_writer":
                        s.status = "done"
                        s.message = f"Completed generating {platform} content."

                # Emit completion steps
                await queue.put(
                    {
                        "event": "step_update",
                        "data": {
                            "id": f"regen_{platform}",
                            "name": f"regen_{platform}",
                            "status": "done",
                            "message": f"Regeneration for {platform} completed successfully.",
                        },
                    }
                )
                await queue.put(
                    {
                        "event": "step_update",
                        "data": {
                            "id": f"{platform}_writer",
                            "name": f"{platform}_writer",
                            "status": "done",
                            "message": f"Completed generating {platform} content.",
                        },
                    }
                )

                outputs_json = {k: v.model_dump(mode="json") for k, v in state.outputs.items()}
                state_dict = state.model_dump(mode="json")
                await job_store.update_job_outputs(job_id, outputs_json, state_dict)
                await job_store.update_job_status(job_id, "completed")

                # Emit new content ready and job complete events
                platform_output = outputs_json.get(platform)
                if platform_output:
                    await queue.put({"event": "content_ready", "data": platform_output})

                cost = state_dict.get("cost")
                await queue.put({"event": "job_complete", "data": {"cost": cost}})

            except Exception as exc:  # noqa: BLE001
                logger.exception("Regenerate %s for job %s failed: %s", platform, job_id, exc)
                state = AgentState(**state_data)
                state.add_step(f"regen_{platform}", "error", f"Regeneration failed: {exc}")
                await job_store.update_job_state(job_id, state.model_dump(mode="json"))
                await job_store.update_job_status(job_id, "failed", error=str(exc))
                await queue.put(
                    {
                        "event": "step_update",
                        "data": {
                            "id": f"regen_{platform}",
                            "name": f"regen_{platform}",
                            "status": "error",
                            "message": f"Regeneration failed: {exc}",
                        },
                    }
                )
                await queue.put({"event": "error", "data": {"message": str(exc)}})
            finally:
                await queue.put(None)

        asyncio.create_task(_regen())
        return True


# ── Singleton ─────────────────────────────────────────────────────────────────
job_service = JobService()
