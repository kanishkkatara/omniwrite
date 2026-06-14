"""
LangGraph StateGraph definition for omniwrite.

Pipeline flow:
  brief_extractor
      ↓ (if complete)
  research
      ↓
  strategy
      ↓
  outline
      ↓ (if approved or approval disabled)
  writers (parallel: blog, reddit, linkedin, linkedin_comment)
      ↓
  editor
      ↓
  END

Human-in-the-loop checkpoints:
  - After brief_extractor: if brief needs clarification → END (wait for user reply)
  - After outline: if outline_approval_enabled → END (wait for approve-outline API call)

Writers run in parallel using asyncio.gather — all are called as a single
"writers" node that fans out internally.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph

from backend.agents.blog_writer import write_blog
from backend.agents.brief_extractor import extract_brief
from backend.agents.editor_agent import run_editor
from backend.agents.linkedin_commenter import write_linkedin_comment
from backend.agents.linkedin_writer import write_linkedin
from backend.agents.outline_agent import create_outline
from backend.agents.reddit_writer import write_reddit
from backend.agents.research_agent import run_research
from backend.agents.strategy_agent import run_strategy
from backend.models.state import AgentState

if TYPE_CHECKING:
    from backend.core.config import Settings

logger = logging.getLogger(__name__)


# ── Node wrappers (bind settings) ─────────────────────────────────────────────

def _make_node(agent_fn, settings: "Settings"):
    """Return an async node function pre-bound to settings."""
    async def node(state_dict: dict[str, Any]) -> dict[str, Any]:
        state = AgentState(**state_dict)
        updated = await agent_fn(state, settings)
        return updated.model_dump()
    return node


def _make_writers_node(settings: "Settings"):
    """Return a parallel writers node that runs all requested platforms concurrently."""
    async def writers_node(state_dict: dict[str, Any]) -> dict[str, Any]:
        state = AgentState(**state_dict)
        request = state.request

        # Determine which platforms to write for
        platforms_to_write: set[str] = set()
        if request and request.platforms:
            platforms_to_write = {p.value for p in request.platforms}
        else:
            platforms_to_write = {"blog", "linkedin", "reddit"}

        # Build coroutines for enabled platforms
        tasks: list = []
        task_names: list[str] = []

        if "blog" in platforms_to_write:
            tasks.append(write_blog(state, settings))
            task_names.append("blog")
        if "reddit" in platforms_to_write:
            tasks.append(write_reddit(state, settings))
            task_names.append("reddit")
        if "linkedin" in platforms_to_write:
            tasks.append(write_linkedin(state, settings))
            task_names.append("linkedin")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Merge outputs and steps from all parallel results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Writer %s failed: %s", task_names[i], result)
                    state.add_step(f"{task_names[i]}_writer", "error", str(result))
                elif isinstance(result, AgentState):
                    # Merge outputs
                    state.outputs.update(result.outputs)
                    # Merge new steps (avoid duplication)
                    existing_step_count = len(state.steps)
                    for step in result.steps[existing_step_count:]:
                        state.steps.append(step)
                    # Accumulate costs
                    state.total_input_tokens = result.total_input_tokens
                    state.total_output_tokens = result.total_output_tokens
                    state.total_cost_usd = result.total_cost_usd

        # LinkedIn comment depends on LinkedIn post being ready
        if "linkedin_comment" in platforms_to_write:
            state = await write_linkedin_comment(state, settings)

        return state.model_dump()

    return writers_node


# ── Conditional edge functions ────────────────────────────────────────────────

def _route_after_brief(state_dict: dict[str, Any]) -> str:
    """Route to research if brief is complete, else END (await user clarification)."""
    brief_data = state_dict.get("brief") or {}
    is_complete = brief_data.get("is_complete", True) if isinstance(brief_data, dict) else getattr(brief_data, "is_complete", True)
    if not is_complete:
        logger.info("Brief incomplete — routing to END (awaiting clarification)")
        return END
    return "research"


def _route_after_outline(state_dict: dict[str, Any]) -> str:
    """Route to writers if outline is approved, else END (await approval)."""
    outline_approved = state_dict.get("outline_approved", True)
    if not outline_approved:
        logger.info("Outline not approved — routing to END (awaiting approval)")
        return END
    return "writers"


# ── Graph factory ─────────────────────────────────────────────────────────────

def create_graph(settings: "Settings"):
    """
    Build and compile the LangGraph StateGraph.

    Args:
        settings: Application settings.

    Returns:
        Compiled LangGraph graph ready for invocation.
    """
    graph = StateGraph(dict)  # use dict as the state type for LangGraph compatibility

    # ── Add nodes ──────────────────────────────────────────────────────────────
    graph.add_node("brief_extractor", _make_node(extract_brief, settings))
    graph.add_node("research", _make_node(run_research, settings))
    graph.add_node("strategy", _make_node(run_strategy, settings))
    graph.add_node("outline", _make_node(create_outline, settings))
    graph.add_node("writers", _make_writers_node(settings))
    graph.add_node("editor", _make_node(run_editor, settings))

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("brief_extractor")

    # ── Edges ──────────────────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "brief_extractor",
        _route_after_brief,
        {END: END, "research": "research"},
    )
    graph.add_edge("research", "strategy")
    graph.add_edge("strategy", "outline")
    graph.add_conditional_edges(
        "outline",
        _route_after_outline,
        {END: END, "writers": "writers"},
    )
    graph.add_edge("writers", "editor")
    graph.add_edge("editor", END)

    compiled = graph.compile()
    logger.info("LangGraph pipeline compiled successfully")
    return compiled
