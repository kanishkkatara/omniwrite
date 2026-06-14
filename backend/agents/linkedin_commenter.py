"""
LinkedIn Commenter Agent.

Uses LinkedInCommentPlugin to generate the author's first comment
on their LinkedIn post. Stores result in state.outputs["linkedin_comment"].
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.models.request import ContentOutput, Platform
from backend.plugins.linkedin_comment_plugin import LinkedInCommentPlugin

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)

_plugin = LinkedInCommentPlugin()


async def write_linkedin_comment(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Generate the LinkedIn first comment and store it in state.outputs["linkedin_comment"].

    Args:
        state: Current AgentState.
        settings: Application settings.

    Returns:
        Updated AgentState with linkedin_comment output populated.
    """
    state.add_step("linkedin_commenter", "running", "Writing LinkedIn first comment…")

    try:
        content = await _plugin.generate(state, settings)

        if content and not content.startswith("[LLM Error"):
            word_count = _plugin.word_count(content)
            state.outputs["linkedin_comment"] = ContentOutput(
                platform=Platform.LINKEDIN_COMMENT,
                content=content,
                word_count=word_count,
                metadata={"plugin": _plugin.name},
            )
            state.add_step(
                "linkedin_commenter",
                "done",
                f"LinkedIn comment written ({word_count} words)",
                {"word_count": word_count},
            )
        else:
            state.add_step("linkedin_commenter", "error", f"LinkedIn comment generation failed: {content}")
            logger.error("LinkedIn commenter error: %s", content)

    except Exception as exc:  # noqa: BLE001
        logger.exception("LinkedIn commenter agent failed: %s", exc)
        state.add_step("linkedin_commenter", "error", str(exc))

    return state
