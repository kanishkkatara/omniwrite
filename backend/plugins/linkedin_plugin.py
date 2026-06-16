"""
LinkedIn post platform plugin.

Generates high-performing LinkedIn posts with:
- Strong hook (first line visible before "see more")
- White-space formatting for readability
- Power sentences and storytelling
- Engagement question or CTA at the end
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


class LinkedInPlugin(PlatformPlugin):
    """Generates LinkedIn-native posts optimised for engagement."""

    name = "linkedin"
    display_name = "LinkedIn Post"
    icon = "💼"
    max_words = 300
    supports_publish = False

    def get_system_prompt(self, brand: BrandProfile | None) -> str:
        brand_context = brand.to_prompt_context() if brand else ""
        base = """You are a LinkedIn native content creator who understands exactly how the algorithm and human psychology intersect on this platform.

LinkedIn post rules:
1. **First line is everything** — it must be scroll-stopping. People see ONLY this line before "see more". Make it a bold statement, surprising fact, contrarian take, or genuine question.
2. **White-space formatting** — use short paragraphs (1–3 lines). Never write a wall of text.
3. **Power sentences** — each line should earn its place. Cut filler words ruthlessly.
4. **Story arc** — even a 200-word post should have: hook → insight/story → lesson/takeaway
5. **No hashtag spam** — max 3–5 relevant hashtags at the very end, or none
6. **End with engagement** — a genuine question to the reader OR a clear CTA (follow, share, comment)
7. **No corporate buzzwords** — no "synergies", "leverage", "paradigm shift"
8. **Emojis sparingly** — 0–3 emojis maximum, only if they add meaning"""

        if brand_context:
            base += f"\n\nBrand profile:\n{brand_context}"

        base += "\n\nOutput the LinkedIn post text ONLY — no labels, no meta-commentary."
        return base

    async def generate(self, state: AgentState, settings: Settings) -> str:
        request = state.request
        brief = state.brief
        strategy = state.strategy

        topic = brief.topic if brief else (request.topic if request else "the topic")
        key_points = brief.key_points if brief else (request.key_points if request else [])
        cta_type = request.cta_type.value if request else "none"
        audience = request.linkedin_audience or (
            ", ".join(state.brand.target_audience)
            if state.brand and state.brand.target_audience
            else ""
        )
        primary_angle = strategy.primary_angle if strategy else ""
        narrative_hook = strategy.narrative_hook if strategy else ""
        platform_tone = ""
        if strategy and strategy.tone_per_platform:
            platform_tone = strategy.tone_per_platform.get("linkedin", "")

        # Hook variants support
        hook_variants = strategy.hook_variants if strategy else []

        user_parts = [f"Write a LinkedIn post about: {topic}"]
        if audience:
            user_parts.append(f"Target audience on LinkedIn: {audience}")
        if primary_angle:
            user_parts.append(f"Core angle: {primary_angle}")
        if narrative_hook:
            user_parts.append(f"Opening hook concept: {narrative_hook}")
        if hook_variants:
            user_parts.append(
                "Hook variant ideas to consider:\n" + "\n".join(f"- {h}" for h in hook_variants[:3])
            )
        if platform_tone:
            user_parts.append(f"Tone: {platform_tone}")
        if key_points:
            user_parts.append(
                "Key insights to include:\n" + "\n".join(f"• {p}" for p in key_points)
            )
        if cta_type and cta_type != "none":
            user_parts.append(f"CTA type: {cta_type.replace('_', ' ')}")
        user_parts.append(
            "Keep the post between 150–280 words. "
            "The FIRST LINE must be the hook. Use plenty of line breaks."
        )

        messages = [
            {"role": "system", "content": self.get_system_prompt(state.brand)},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        content, input_tok, output_tok, cost = await llm_call(
            messages=messages,
            agent_name="linkedin_writer",
            settings=settings,
        )

        state.add_cost(input_tok, output_tok, cost)
        logger.info("LinkedInPlugin generated %d words", self.word_count(content))
        return content
