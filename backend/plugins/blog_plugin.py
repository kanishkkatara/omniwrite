"""
Blog post platform plugin.

Generates long-form, SEO-optimised Markdown blog posts with:
- Compelling intro hook
- H2/H3-structured body sections
- Conclusion + CTA
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


class BlogPlugin(PlatformPlugin):
    """Generates long-form blog posts in Markdown."""

    name = "blog"
    display_name = "Blog Post"
    icon = "📝"
    max_words = 3000
    supports_publish = False

    def get_system_prompt(self, brand: BrandProfile | None) -> str:
        brand_context = (
            brand.to_prompt_context() if brand else "No specific brand profile provided."
        )
        return f"""You are an expert long-form content writer and SEO strategist.

Your role:
- Write engaging, well-researched blog posts in Markdown
- Structure content with a compelling intro hook, scannable H2/H3 sections, and a strong conclusion
- Naturally weave in SEO keywords without keyword stuffing
- Match the brand's voice and tone precisely
- Every piece should provide genuine value to the reader

Brand & voice context:
{brand_context}

Formatting rules:
- Use Markdown (##, ###, **bold**, bullet lists, numbered lists)
- Start with a title as # Heading
- First paragraph must hook the reader within 2–3 sentences
- Use H2 for major sections, H3 for sub-points
- Include a "Key Takeaways" or summary section near the end
- End with a clear, natural call-to-action
- Do NOT use placeholder text or template markers
- Write in a natural, human voice — not AI-robotic

Output the blog post ONLY — no preamble or meta-commentary."""

    async def generate(self, state: AgentState, settings: Settings) -> str:  # noqa: C901
        request = state.request
        brief = state.brief
        strategy = state.strategy

        topic = brief.topic if brief else (request.topic if request else "the topic")
        key_points = brief.key_points if brief else (request.key_points if request else [])
        seo_keywords = brief.seo_keywords if brief else (request.seo_keywords if request else [])
        reading_level = request.reading_level.value if request else "intermediate"
        cta_type = request.cta_type.value if request else "none"
        length = request.length.value if request else "medium"

        # Length guidance
        length_map = {
            "short": "600–900 words",
            "medium": "1000–1400 words",
            "long": "1800–2500 words",
        }
        length_guide = length_map.get(length, "1000–1400 words")

        primary_angle = strategy.primary_angle if strategy else ""
        narrative_hook = strategy.narrative_hook if strategy else ""
        outline = state.outline or ""
        research_summary = state.research_summary or ""

        user_parts = [
            f"Write a {length_guide} blog post about: **{topic}**",
            f"Reading level: {reading_level}",
        ]
        if primary_angle:
            user_parts.append(f"Primary angle: {primary_angle}")
        if narrative_hook:
            user_parts.append(f"Opening hook concept: {narrative_hook}")
        if key_points:
            user_parts.append("Key points to cover:\n" + "\n".join(f"- {p}" for p in key_points))
        if seo_keywords:
            user_parts.append(f"SEO keywords to include naturally: {', '.join(seo_keywords)}")
        if outline:
            user_parts.append(f"\nApproved outline to follow:\n{outline}")
        if research_summary:
            user_parts.append(f"\nResearch context to draw from:\n{research_summary}")
        if cta_type and cta_type != "none":
            user_parts.append(f"Call-to-action type at the end: {cta_type.replace('_', ' ')}")

        messages = [
            {"role": "system", "content": self.get_system_prompt(state.brand)},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        content, input_tok, output_tok, cost = await llm_call(
            messages=messages,
            agent_name="blog_writer",
            settings=settings,
        )

        state.add_cost(input_tok, output_tok, cost)
        logger.info("BlogPlugin generated %d words", self.word_count(content))
        return content
