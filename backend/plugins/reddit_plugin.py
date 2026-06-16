"""
Reddit post platform plugin.

Generates native-sounding Reddit posts with:
- Strong hook title
- Conversational, opinionated body
- TL;DR summary
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call
from backend.plugins.base import PlatformPlugin

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.brand import BrandProfile
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)


class RedditPlugin(PlatformPlugin):
    """Generates Reddit-style posts that sound authentically human."""

    name = "reddit"
    display_name = "Reddit Post"
    icon = "🤖"
    max_words = 800
    supports_publish = False

    def get_system_prompt(self, brand: BrandProfile | None) -> str:
        brand_context = brand.to_prompt_context() if brand else ""
        base = """You are a native Reddit user and expert communicator writing in authentic Reddit style.

Your rules:
- NO corporate speak, marketing fluff, or press-release language
- Write like a real person sharing a genuine experience, opinion, or insight
- Be conversational, direct, and a little opinionated — Redditors respect confidence
- Start with a title that is curious, provocative, or immediately valuable
- Keep the body focused — Redditors don't read walls of text
- Use paragraph breaks generously (2–4 sentences max per paragraph)
- You CAN use light formatting: **bold** for emphasis, occasional bullet lists
- End with a TL;DR (always — even if the post is short)
- No hashtags, no "follow me", no overt self-promotion
- Sound like you discovered something cool and want to share it"""

        if brand_context:
            base += (
                f"\n\nBrand context (for background, not for copying verbatim):\n{brand_context}"
            )

        base += "\n\nOutput format:\n**Title:** [your title]\n\n[post body]\n\n**TL;DR:** [1–2 sentence summary]"
        base += "\n\nOutput the Reddit post ONLY."
        return base

    async def generate(self, state: AgentState, settings: Settings) -> str:
        request = state.request
        brief = state.brief
        strategy = state.strategy

        topic = brief.topic if brief else (request.topic if request else "the topic")
        key_points = brief.key_points if brief else (request.key_points if request else [])
        subreddit = request.reddit_subreddit if request else None
        research_summary = state.research_summary or ""
        primary_angle = strategy.primary_angle if strategy else ""
        narrative_hook = strategy.narrative_hook if strategy else ""
        platform_tone = ""
        if strategy and strategy.tone_per_platform:
            platform_tone = strategy.tone_per_platform.get("reddit", "")

        user_parts = [f"Write a Reddit post about: {topic}"]
        if subreddit:
            user_parts.append(
                f"Target subreddit: r/{subreddit} — calibrate tone and specificity for that community"
            )
        if primary_angle:
            user_parts.append(f"Angle: {primary_angle}")
        if narrative_hook:
            user_parts.append(f"Hook concept: {narrative_hook}")
        if platform_tone:
            user_parts.append(f"Tone guidance: {platform_tone}")
        if key_points:
            user_parts.append("Points to weave in:\n" + "\n".join(f"- {p}" for p in key_points))
        if research_summary:
            user_parts.append(f"Supporting research/facts:\n{research_summary}")
        user_parts.append("Keep it under 600 words. Make it feel genuine, not like an ad.")

        messages = [
            {"role": "system", "content": self.get_system_prompt(state.brand)},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        content, input_tok, output_tok, cost = await llm_call(
            messages=messages,
            agent_name="reddit_writer",
            settings=settings,
        )

        state.add_cost(input_tok, output_tok, cost)
        logger.info("RedditPlugin generated %d words", self.word_count(content))
        return content
