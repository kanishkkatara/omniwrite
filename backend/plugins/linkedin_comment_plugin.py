"""
LinkedIn first-comment plugin.

Generates the author's first comment under their own LinkedIn post.
This is a high-engagement tactic where the author adds context,
a link, or sparks discussion immediately after publishing.
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


class LinkedInCommentPlugin(PlatformPlugin):
    """Generates the author's first comment on their own LinkedIn post."""

    name = "linkedin_comment"
    display_name = "LinkedIn First Comment"
    icon = "💬"
    max_words = 150
    supports_publish = False

    def get_system_prompt(self, brand: BrandProfile | None) -> str:
        brand_context = brand.to_prompt_context() if brand else ""
        base = """You write the author's first comment on their own LinkedIn post.

This comment serves one of these purposes:
1. Add a useful resource/link that would clutter the main post
2. Give additional context, backstory, or personal anecdote
3. Ask a follow-up question to spark discussion
4. Drop a key statistic or quote that reinforces the post

Rules:
- Write it in the SAME voice as the main post (same person commenting)
- Keep it SHORT — 50–120 words maximum
- It should feel like a natural follow-up, not an advertisement
- If a URL might be included, write [link] as a placeholder
- Start with something that connects to the post (not "Also..." or "BTW...")
- Make the reader feel like they're getting bonus value
- No emojis unless absolutely natural
- No "Like and follow for more!" type language"""

        if brand_context:
            base += f"\n\nBrand/author context:\n{brand_context}"

        base += "\n\nOutput the comment text ONLY."
        return base

    async def generate(self, state: AgentState, settings: Settings) -> str:
        request = state.request
        brief = state.brief
        strategy = state.strategy

        topic = brief.topic if brief else (request.topic if request else "the topic")
        key_points = brief.key_points if brief else (request.key_points if request else [])
        source_urls = brief.source_urls if brief else (request.source_urls if request else [])
        cta_type = request.cta_type.value if request else "none"
        primary_angle = strategy.primary_angle if strategy else ""

        # Reference the LinkedIn post if available
        linkedin_post = state.outputs.get("linkedin")
        linkedin_post_text = ""
        if linkedin_post:
            # Truncate to keep context brief
            linkedin_post_text = linkedin_post.content[:500]

        user_parts = [
            f"Write the first comment that the author would post under their LinkedIn post about: {topic}"
        ]
        if linkedin_post_text:
            user_parts.append(
                f"The LinkedIn post text (for context):\n---\n{linkedin_post_text}\n---"
            )
        if primary_angle:
            user_parts.append(f"Main angle of the post: {primary_angle}")
        if key_points:
            user_parts.append("Topics covered:\n" + "\n".join(f"- {p}" for p in key_points))
        if source_urls:
            user_parts.append(f"Possible resource links to reference: {', '.join(source_urls[:2])}")
        if cta_type and cta_type != "none":
            user_parts.append(
                f"The post's CTA is: {cta_type.replace('_', ' ')} — the comment should reinforce this"
            )
        user_parts.append("Keep the comment under 100 words. Make it feel human and valuable.")

        messages = [
            {"role": "system", "content": self.get_system_prompt(state.brand)},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        content, input_tok, output_tok, cost = await llm_call(
            messages=messages,
            agent_name="linkedin_commenter",
            settings=settings,
        )

        state.add_cost(input_tok, output_tok, cost)
        logger.info("LinkedInCommentPlugin generated %d words", self.word_count(content))
        return content
