"""
Reddit Writer Agent.

Uses RedditPlugin to generate a Reddit post and stores the result
in state.outputs["reddit"].
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.models.request import ContentOutput, Platform
from backend.plugins.reddit_plugin import RedditPlugin

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)

_plugin = RedditPlugin()


async def write_reddit(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Generate a Reddit post and store it in state.outputs["reddit"].

    Args:
        state: Current AgentState.
        settings: Application settings.

    Returns:
        Updated AgentState with reddit output populated.
    """
    state.add_step("reddit_writer", "running", "Writing Reddit post…")

    try:
        content = await _plugin.generate(state, settings)

        if content and not content.startswith("[LLM Error"):
            word_count = _plugin.word_count(content)
            state.outputs["reddit"] = ContentOutput(
                platform=Platform.REDDIT,
                content=content,
                word_count=word_count,
                metadata={"plugin": _plugin.name},
            )
            state.add_step(
                "reddit_writer",
                "done",
                f"Reddit post written ({word_count} words)",
                {"word_count": word_count},
            )
        else:
            state.add_step("reddit_writer", "error", f"Reddit generation failed: {content}")
            logger.error("Reddit writer error: %s", content)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Reddit writer agent failed: %s", exc)
        state.add_step("reddit_writer", "error", str(exc))

    return state
