"""
Brief Extractor Agent.

Parses the user's latest message into a structured ContentBrief.
If the brief needs clarification, sets clarifying_questions and returns
without marking it complete, prompting the API to ask the user for more info.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call
from backend.models.state import ContentBrief

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)


async def extract_brief(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Parse the user's last message into a ContentBrief.

    If state.request already has a topic set (API mode), uses that to build
    a minimal brief directly. Otherwise, processes state.messages[-1].content.

    Returns:
        Updated AgentState with state.brief populated.
    """
    state.add_step("brief_extractor", "running", "Extracting content brief…")

    try:
        # Fast-path: if request is already structured, build brief directly
        if state.request and state.request.topic:
            brief = ContentBrief(
                topic=state.request.topic,
                key_points=state.request.key_points or [],
                seo_keywords=state.request.seo_keywords or [],
                source_urls=state.request.source_urls or [],
                sample_draft=state.request.sample_draft,
                clarifying_questions=[],
                is_complete=True,
            )
            state.brief = brief
            state.add_step("brief_extractor", "done", f"Brief ready: {brief.topic}")
            return state

        # Chat mode: extract from the last message
        if not state.messages:
            state.brief = ContentBrief(topic="Unknown topic", is_complete=False)
            state.add_step("brief_extractor", "error", "No messages found in state")
            return state

        last_message = state.messages[-1]
        user_content: str = (
            last_message.content
            if hasattr(last_message, "content")
            else str(last_message)
        )

        brand_context = state.brand.to_prompt_context() if state.brand else ""

        system_prompt = (
            "You are a content strategist who extracts structured briefs from user requests.\n\n"
            "Parse the user's input and return ONLY valid JSON with these fields:\n"
            "- topic (string, required)\n"
            "- key_points (array of strings)\n"
            "- seo_keywords (array of strings)\n"
            "- source_urls (array of strings)\n"
            "- target_audience_override (string or null)\n"
            "- clarifying_questions (array of strings — empty if brief is clear)\n"
            "- is_complete (boolean)\n\n"
            "Return ONLY valid JSON."
        )

        user_prompt_parts = [f"Extract a content brief from:\n\n{user_content}"]
        if brand_context:
            user_prompt_parts.append(f"Brand context:\n{brand_context}")
        user_prompt_parts.append("Return ONLY valid JSON.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(user_prompt_parts)},
        ]

        response_text, in_tok, out_tok, cost = await llm_call(
            messages=messages,
            agent_name="brief_extractor",
            settings=settings,
        )
        state.add_cost(in_tok, out_tok, cost)

        # Parse JSON response
        try:
            # Strip potential markdown code fences
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```", 2)[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.rstrip("`").strip()

            data = json.loads(clean)
            brief = ContentBrief(
                topic=data.get("topic", user_content[:200]),
                key_points=data.get("key_points", []),
                seo_keywords=data.get("seo_keywords", []),
                source_urls=data.get("source_urls", []),
                target_audience_override=data.get("target_audience_override"),
                clarifying_questions=data.get("clarifying_questions", []),
                is_complete=data.get("is_complete", True),
            )
        except json.JSONDecodeError:
            logger.warning("Brief extractor returned non-JSON; falling back to raw content")
            brief = ContentBrief(
                topic=user_content[:300],
                is_complete=True,
            )

        state.brief = brief
        if brief.is_complete:
            state.add_step("brief_extractor", "done", f"Brief ready: {brief.topic}")
        else:
            state.add_step(
                "brief_extractor",
                "waiting",
                "Clarification needed",
                {"questions": brief.clarifying_questions},
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Brief extractor failed: %s", exc)
        state.error = str(exc)
        state.add_step("brief_extractor", "error", str(exc))
        # Create minimal fallback brief
        topic = state.request.topic if state.request else "Unknown topic"
        state.brief = ContentBrief(topic=topic, is_complete=True)

    return state
