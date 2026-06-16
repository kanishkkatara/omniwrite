"""
LinkedIn Writer Agent.

Uses LinkedInPlugin to generate a LinkedIn post and stores the result
in state.outputs["linkedin"].
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.models.request import ContentOutput, Platform
from backend.plugins.linkedin_plugin import LinkedInPlugin

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)

_plugin = LinkedInPlugin()


async def write_linkedin(state: AgentState, settings: Settings) -> AgentState:
    """
    Generate a LinkedIn post and store it in state.outputs["linkedin"].

    Args:
        state: Current AgentState.
        settings: Application settings.

    Returns:
        Updated AgentState with linkedin output populated.
    """
    state.add_step("linkedin_writer", "running", "Writing LinkedIn post…")

    try:
        content = await _plugin.generate(state, settings)

        if content and not content.startswith("[LLM Error"):
            word_count = _plugin.word_count(content)
            state.outputs["linkedin"] = ContentOutput(
                platform=Platform.LINKEDIN,
                content=content,
                word_count=word_count,
                metadata={"plugin": _plugin.name},
            )
            state.add_step(
                "linkedin_writer",
                "done",
                f"LinkedIn post written ({word_count} words)",
                {"word_count": word_count},
            )
        else:
            state.add_step("linkedin_writer", "error", f"LinkedIn generation failed: {content}")
            logger.error("LinkedIn writer error: %s", content)

    except Exception as exc:  # noqa: BLE001
        logger.exception("LinkedIn writer agent failed: %s", exc)
        state.add_step("linkedin_writer", "error", str(exc))

    return state
