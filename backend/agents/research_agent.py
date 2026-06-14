"""
Research Agent.

Runs targeted web searches based on the extracted brief topic,
deduplicates results, and generates a concise research summary via LLM.

Skips if:
- state.request.skip_research is True
- settings.research_enabled is False
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.core.llm_factory import llm_call
from backend.providers.search import get_search_provider

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import AgentState, SearchResult

logger = logging.getLogger(__name__)


def _deduplicate(results: list["SearchResult"]) -> list["SearchResult"]:
    """Remove duplicate results by URL."""
    seen: set[str] = set()
    unique: list["SearchResult"] = []
    for r in results:
        if r.url and r.url not in seen:
            seen.add(r.url)
            unique.append(r)
    return unique


def _build_search_queries(topic: str, key_points: list[str]) -> list[str]:
    """Generate 2–3 targeted search queries from topic and key points."""
    queries = [topic]
    if key_points:
        # Use the first key point to create a second query
        queries.append(f"{topic} {key_points[0]}")
    if len(key_points) > 1:
        queries.append(f"{topic} {key_points[1]} best practices")
    return queries[:3]


async def run_research(state: "AgentState", settings: "Settings") -> "AgentState":
    """
    Run web research for the content brief.

    Args:
        state: Current AgentState (expects state.brief to be populated).
        settings: Application settings.

    Returns:
        Updated AgentState with research_results and research_summary populated.
    """
    # Check if research should be skipped
    if state.request and state.request.skip_research:
        logger.info("Research skipped by request flag")
        state.add_step("research", "done", "Research skipped (skip_research=True)")
        return state

    if not settings.research_enabled:
        logger.info("Research disabled in settings")
        state.add_step("research", "done", "Research disabled in settings")
        return state

    state.add_step("research", "running", "Researching topic…")

    try:
        brief = state.brief
        if not brief:
            state.add_step("research", "done", "No brief available, skipping research")
            return state

        topic = brief.topic
        key_points = brief.key_points or []

        # Also search any URLs from the brief
        extra_queries: list[str] = []
        if brief.source_urls:
            extra_queries.append(f"site information from {' '.join(brief.source_urls[:2])}")

        queries = _build_search_queries(topic, key_points)
        if extra_queries:
            queries = (queries + extra_queries)[:3]

        provider = get_search_provider(settings)
        all_results: list["SearchResult"] = []

        for query in queries:
            logger.debug("Searching: %s", query)
            results = await provider.search(query, num_results=5)
            all_results.extend(results)

        unique_results = _deduplicate(all_results)[:12]  # cap at 12 results
        state.research_results = unique_results

        if not unique_results:
            state.research_summary = ""
            state.add_step("research", "done", "No research results found")
            return state

        # Summarise results via LLM
        results_text = "\n\n".join(
            f"[{i+1}] {r.title}\nURL: {r.url}\n{r.snippet}"
            for i, r in enumerate(unique_results)
        )

        summary_messages = [
            {
                "role": "system",
                "content": (
                    "You are a research analyst. Given web search results, "
                    "create a concise, factual research summary of 200–400 words. "
                    "Extract key facts, statistics, trends, and insights relevant to the topic. "
                    "Be objective. Do not include URLs in the summary. "
                    "Use clear, flowing prose — not bullet points."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Summarise these search results for the topic: **{topic}**\n\n"
                    f"{results_text}\n\n"
                    "Write a 200–400 word factual summary of the most relevant findings."
                ),
            },
        ]

        summary_text, in_tok, out_tok, cost = await llm_call(
            messages=summary_messages,
            agent_name="research",
            settings=settings,
        )
        state.add_cost(in_tok, out_tok, cost)
        state.research_summary = summary_text

        state.add_step(
            "research",
            "done",
            f"Research complete: {len(unique_results)} sources, {len(summary_text)} chars summary",
            {"source_count": len(unique_results), "provider": provider.name},
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Research agent failed: %s", exc)
        state.research_summary = ""
        state.add_step("research", "error", f"Research failed: {exc}")
        # Don't set state.error — research failure is non-fatal

    return state
