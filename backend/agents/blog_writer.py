"""
Blog Writer Agent.

Uses BlogPlugin to generate a long-form blog post and stores the result
in state.outputs["blog"].
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.models.request import ContentOutput, Platform
from backend.plugins.blog_plugin import BlogPlugin

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)

_plugin = BlogPlugin()


async def write_blog(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Generate a blog post and store it in state.outputs["blog"].

    Args:
        state: Current AgentState.
        settings: Application settings.

    Returns:
        Updated AgentState with blog output populated.
    """
    state.add_step("blog_writer", "running", "Writing blog post…")

    try:
        # Use the user-edited outline if available
        if state.outline_edited:
            state.outline = state.outline_edited

        content = await _plugin.generate(state, settings)

        if content and not content.startswith("[LLM Error"):
            word_count = _plugin.word_count(content)
            state.outputs["blog"] = ContentOutput(
                platform=Platform.BLOG,
                content=content,
                word_count=word_count,
                metadata={"plugin": _plugin.name},
            )
            state.add_step(
                "blog_writer",
                "done",
                f"Blog post written ({word_count} words)",
                {"word_count": word_count},
            )
        else:
            state.add_step("blog_writer", "error", f"Blog generation failed: {content}")
            logger.error("Blog writer error: %s", content)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Blog writer agent failed: %s", exc)
        state.add_step("blog_writer", "error", str(exc))

    return state
