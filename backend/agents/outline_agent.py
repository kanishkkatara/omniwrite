"""
Outline Agent.

Creates a structured, human-reviewable blog post outline.
Sets state.outline_approved = False to pause the graph for human review
when outline approval is enabled in settings.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)


async def create_outline(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Generate a Markdown blog post outline based on strategy.

    Args:
        state: Current AgentState (expects state.strategy to be populated).
        settings: Application settings.

    Returns:
        Updated AgentState with state.outline set.
        Sets state.outline_approved = False if approval is enabled.
    """
    state.add_step("outline", "running", "Creating content outline…")

    try:
        brief = state.brief
        strategy = state.strategy
        request = state.request

        topic = brief.topic if brief else (request.topic if request else "the topic")
        key_points = brief.key_points if brief else (request.key_points if request else [])
        seo_keywords = brief.seo_keywords if brief else (request.seo_keywords if request else [])
        research_summary = state.research_summary or ""
        length = request.length.value if request else "medium"
        reading_level = request.reading_level.value if request else "intermediate"

        primary_angle = strategy.primary_angle if strategy else ""
        narrative_hook = strategy.narrative_hook if strategy else ""
        suggested_structure = strategy.suggested_structure if strategy else []

        system_prompt = (
            "You are a content architect who creates detailed, actionable blog post outlines.\n\n"
            "Format the outline in clean Markdown with:\n"
            "1. **Title Options** (2–3 variants)\n"
            "2. **Meta Description** (155 chars, SEO-optimised)\n"
            "3. **Intro Concept** (2–3 sentences describing the hook approach)\n"
            "4. **Main Sections** (H2 level) each with:\n"
            "   - Section title\n"
            "   - 2–4 bullet points describing what to cover\n"
            "   - Estimated word count\n"
            "5. **Conclusion Approach**\n"
            "6. **CTA**\n"
            "7. **SEO Notes** (primary keyword, secondary keywords)\n\n"
            "Be specific — avoid vague section names. Output Markdown ONLY."
        )

        user_parts = [
            f"Create a detailed blog post outline for: **{topic}**",
            f"Target length: {length}",
            f"Reading level: {reading_level}",
        ]
        if primary_angle:
            user_parts.append(f"Primary angle: {primary_angle}")
        if narrative_hook:
            user_parts.append(f"Narrative hook concept: {narrative_hook}")
        if key_points:
            user_parts.append("Key points to include:\n" + "\n".join(f"- {p}" for p in key_points))
        if seo_keywords:
            user_parts.append(f"SEO keywords: {', '.join(seo_keywords)}")
        if suggested_structure:
            user_parts.append(
                "Suggested section structure:\n" + "\n".join(f"- {s}" for s in suggested_structure)
            )
        if research_summary:
            user_parts.append(f"Research context:\n{research_summary}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        outline_text, in_tok, out_tok, cost = await llm_call(
            messages=messages,
            agent_name="outline",
            settings=settings,
        )
        state.add_cost(in_tok, out_tok, cost)

        state.outline = outline_text or ""

        # Determine if approval is needed
        outline_approval_enabled = settings.generation.outline_approval_enabled
        skip_approval = request.skip_outline_approval if request else False

        if outline_approval_enabled and not skip_approval:
            state.outline_approved = False
            state.add_step(
                "outline",
                "waiting_approval",
                "Outline ready — awaiting human approval",
                {"outline_length": len(outline_text or "")},
            )
        else:
            state.outline_approved = True
            state.add_step(
                "outline",
                "done",
                "Outline created and auto-approved",
                {"outline_length": len(outline_text or "")},
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Outline agent failed: %s", exc)
        state.outline = ""
        state.outline_approved = True  # Don't block pipeline on outline failure
        state.add_step("outline", "error", str(exc))

    return state
