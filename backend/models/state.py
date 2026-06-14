"""LangGraph AgentState — the shared state object flowing through the agent graph."""
from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from backend.models.brand import BrandProfile
from backend.models.request import ContentLength, ContentOutput, CTAType, GenerateRequest, GenerationCost, ModelMode, Platform, ReadingLevel


class AgentStep(BaseModel):
    """Represents one completed agent step for streaming to the frontend."""
    agent: str
    status: str  # running | done | error
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = ""


class ContentBrief(BaseModel):
    """Structured brief extracted from the user's chat input."""
    topic: str
    key_points: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)
    target_audience_override: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    sample_draft: str | None = None
    clarifying_questions: list[str] = Field(default_factory=list)
    is_complete: bool = False  # True once user has answered clarifying questions


class ContentStrategy(BaseModel):
    """Output of the Strategy Agent."""
    primary_angle: str
    narrative_hook: str
    tone_per_platform: dict[str, str] = Field(default_factory=dict)
    hook_variants: list[str] = Field(default_factory=list)
    audience_assumptions: str = ""
    suggested_structure: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    """
    The central state object for the LangGraph pipeline.
    All agents read from and write to this state.
    """

    # ── Job identity ─────────────────────────────────────────────────────────
    job_id: UUID
    brand: BrandProfile | None = None
    request: GenerateRequest | None = None

    # ── Chat messages (LangGraph message accumulator) ─────────────────────────
    messages: Annotated[list[Any], add_messages] = Field(default_factory=list)

    # ── Pipeline stages ───────────────────────────────────────────────────────
    brief: ContentBrief | None = None
    research_results: list[SearchResult] = Field(default_factory=list)
    research_summary: str = ""
    strategy: ContentStrategy | None = None

    # ── Outline (human-in-the-loop) ───────────────────────────────────────────
    outline: str = ""
    outline_approved: bool = False
    outline_edited: str | None = None  # user-edited version

    # ── Outputs ───────────────────────────────────────────────────────────────
    outputs: dict[str, ContentOutput] = Field(default_factory=dict)

    # ── Progress tracking ─────────────────────────────────────────────────────
    steps: list[AgentStep] = Field(default_factory=list)
    current_step: str = "pending"
    error: str | None = None

    # ── Cost tracking ─────────────────────────────────────────────────────────
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    start_time: float | None = None
    end_time: float | None = None

    class Config:
        arbitrary_types_allowed = True

    def add_step(self, agent: str, status: str, message: str = "", data: dict | None = None) -> None:
        self.steps.append(
            AgentStep(agent=agent, status=status, message=message, data=data or {})
        )
        self.current_step = agent

    def add_cost(self, input_tokens: int, output_tokens: int, cost: float) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
