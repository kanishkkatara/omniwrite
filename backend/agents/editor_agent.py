"""
Editor Agent.

Reviews all platform outputs for:
- Consistency with the brief (same facts, same brand voice)
- Factual alignment with research
- Platform-appropriate tone
- Minor grammar/spelling fixes

Always uses the PRODUCTION model for quality assurance.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call
from backend.models.request import ModelMode

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)


async def run_editor(state: AgentState, settings: Settings) -> AgentState:
    """
    Review and lightly edit all generated outputs.

    The editor uses the PRODUCTION model regardless of request model_mode
    for consistent quality review.

    Args:
        state: Current AgentState with outputs populated.
        settings: Application settings.

    Returns:
        Updated AgentState with potentially edited outputs and editor notes.
    """
    state.add_step("editor", "running", "Reviewing and editing all outputs…")

    if not state.outputs:
        state.add_step("editor", "done", "No outputs to review")
        return state

    try:
        brief = state.brief
        topic = brief.topic if brief else (state.request.topic if state.request else "the topic")
        brand_name = state.brand.name if state.brand else "Unknown brand"
        research_summary = state.research_summary or ""

        # Build outputs text for review
        outputs_text_parts = []
        for platform_key, output in state.outputs.items():
            outputs_text_parts.append(f"### {platform_key.upper()}\n{output.content}")

        system_prompt = (
            "You are a senior content editor. Review all platform outputs and make MINIMAL necessary corrections.\n\n"
            "Check for:\n"
            "1. Factual consistency with the research provided\n"
            "2. Brand voice consistency across all platforms\n"
            "3. Platform-appropriate tone (Reddit ≠ LinkedIn ≠ Blog)\n"
            "4. Grammar and spelling errors\n"
            "5. Broken Markdown formatting\n\n"
            "Rules:\n"
            "- Make only NECESSARY changes — preserve the writer's voice\n"
            "- Never rewrite entirely — fix specific issues\n"
            "- If content is great, return it unchanged\n\n"
            "Return valid JSON:\n"
            '{"outputs": {"<platform>": "<edited or original content>", ...}, "editor_notes": "<summary of changes>"}\n\n'
            "Include only platforms that were in the input. Return ONLY valid JSON."
        )

        outputs_block = "\n\n".join(outputs_text_parts)
        user_prompt = f"Topic: {topic}\nBrand: {brand_name}\n"
        if research_summary:
            user_prompt += f"\nResearch context:\n{research_summary[:800]}\n"
        user_prompt += (
            f"\n--- OUTPUTS TO REVIEW ---\n\n{outputs_block}\n\n---\n\nReturn ONLY valid JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Always use production model for editing
        response_text, in_tok, out_tok, cost = await llm_call(
            messages=messages,
            agent_name="editor",
            model_mode=ModelMode.PRODUCTION,
            settings=settings,
        )
        state.add_cost(in_tok, out_tok, cost)

        # Parse editor response
        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                parts = clean.split("```", 2)
                clean = parts[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip().rstrip("`").strip()

            data = json.loads(clean)
            edited_outputs = data.get("outputs", {})
            editor_notes = data.get("editor_notes", "No notes provided")

            # Update outputs with edited content
            for platform_key, edited_content in edited_outputs.items():
                if platform_key in state.outputs and isinstance(edited_content, str):
                    original = state.outputs[platform_key]
                    from backend.models.request import ContentOutput  # noqa: PLC0415

                    state.outputs[platform_key] = ContentOutput(
                        platform=original.platform,
                        content=edited_content,
                        word_count=len(edited_content.split()),
                        metadata={**original.metadata, "edited": True},
                    )

            state.add_step(
                "editor",
                "done",
                f"Review complete: {editor_notes[:100]}",
                {"editor_notes": editor_notes, "platforms_reviewed": list(state.outputs.keys())},
            )

        except (json.JSONDecodeError, TypeError) as parse_exc:
            logger.warning("Editor returned non-JSON (%s); keeping original outputs", parse_exc)
            state.add_step(
                "editor", "done", "Review complete (parser warning — originals preserved)"
            )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Editor agent failed: %s", exc)
        state.add_step("editor", "error", f"Editor failed: {exc}")
        # Non-fatal — keep original outputs

    return state
