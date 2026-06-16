"""
Strategy Agent.

Uses the content brief, research summary, and brand context to generate
a ContentStrategy with primary angle, narrative hook, per-platform tones,
and hook variants.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call
from backend.models.state import ContentStrategy

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState

logger = logging.getLogger(__name__)


async def run_strategy(state: AgentState, settings: Settings) -> AgentState:
    """
    Generate a ContentStrategy from the brief, research, and brand context.

    Args:
        state: Current AgentState (expects state.brief to be populated).
        settings: Application settings.

    Returns:
        Updated AgentState with state.strategy populated.
    """
    state.add_step("strategy", "running", "Developing content strategy…")

    try:
        brief = state.brief
        if not brief:
            state.add_step("strategy", "error", "No brief available for strategy")
            state.strategy = ContentStrategy(
                primary_angle=state.request.topic if state.request else "General overview",
                narrative_hook="Start with a surprising fact or question",
                tone_per_platform={},
                hook_variants=[],
            )
            return state

        topic = brief.topic
        key_points = brief.key_points or []
        research_summary = state.research_summary or ""
        brand_context = state.brand.to_prompt_context() if state.brand else ""
        platforms = (
            [p.value for p in state.request.platforms]
            if state.request
            else ["blog", "linkedin", "reddit"]
        )
        num_variants = state.request.variants if state.request else 1

        system_prompt = (
            "You are a senior content strategist. "
            "Generate a content strategy and return ONLY valid JSON with these exact fields:\n"
            '- "primary_angle": string (the strongest unique angle, 1–2 sentences)\n'
            '- "narrative_hook": string (the hook concept — the idea, not the written text)\n'
            '- "tone_per_platform": object with platform keys and tone description strings\n'
            f'- "hook_variants": array of {num_variants} distinct hook opening concepts\n'
            '- "audience_assumptions": string (who you assume is reading)\n'
            '- "suggested_structure": array of 4–6 high-level blog section titles\n\n'
            "Return ONLY valid JSON."
        )

        user_parts = [f"Topic: {topic}"]
        if key_points:
            user_parts.append("Key points:\n" + "\n".join(f"- {p}" for p in key_points))
        if research_summary:
            user_parts.append(f"Research summary:\n{research_summary}")
        if brand_context:
            user_parts.append(f"Brand profile:\n{brand_context}")
        user_parts.append(f"Target platforms: {', '.join(platforms)}")
        user_parts.append(f"Number of hook variants needed: {num_variants}")
        user_parts.append("Return ONLY valid JSON.")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        response_text, in_tok, out_tok, cost = await llm_call(
            messages=messages,
            agent_name="strategy",
            settings=settings,
        )
        state.add_cost(in_tok, out_tok, cost)

        # Parse JSON
        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                parts = clean.split("```", 2)
                clean = parts[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip().rstrip("`").strip()

            data = json.loads(clean)
            strategy = ContentStrategy(
                primary_angle=data.get("primary_angle", "A fresh perspective on " + topic),
                narrative_hook=data.get("narrative_hook", "Open with a surprising fact"),
                tone_per_platform=data.get("tone_per_platform", {}),
                hook_variants=data.get("hook_variants", []),
                audience_assumptions=data.get("audience_assumptions", ""),
                suggested_structure=data.get("suggested_structure", []),
            )
        except (json.JSONDecodeError, TypeError) as parse_exc:
            logger.warning("Strategy agent returned non-JSON: %s", parse_exc)
            strategy = ContentStrategy(
                primary_angle=f"A practical guide to {topic}",
                narrative_hook="Open with the most surprising finding from research",
                tone_per_platform={
                    "blog": "informative and engaging",
                    "linkedin": "professional yet personal",
                    "reddit": "conversational and direct",
                    "linkedin_comment": "helpful and concise",
                },
                hook_variants=[f"Most people think {topic} is straightforward. It's not."],
            )

        state.strategy = strategy
        state.add_step(
            "strategy",
            "done",
            f"Strategy ready: {strategy.primary_angle[:80]}…",
            {"angle": strategy.primary_angle},
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Strategy agent failed: %s", exc)
        state.add_step("strategy", "error", str(exc))
        # Non-fatal fallback
        topic = state.brief.topic if state.brief else "the topic"
        state.strategy = ContentStrategy(
            primary_angle=f"A comprehensive overview of {topic}",
            narrative_hook="Start with an unexpected insight",
            tone_per_platform={},
            hook_variants=[],
        )

    return state
