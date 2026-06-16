"""
Unit tests for omniwrite agents and state.
"""

from __future__ import annotations

import time
from uuid import uuid4

from backend.core.config import get_settings
from backend.models.request import GenerateRequest, ModelMode, Platform
from backend.models.state import AgentState


def test_agent_state_initialization():
    """Test that AgentState initializes with correct default values."""
    job_id = uuid4()
    request = GenerateRequest(
        topic="AI Agents in production",
        platforms=[Platform.BLOG, Platform.LINKEDIN],
        model_mode=ModelMode.TEST,
    )

    state = AgentState(
        job_id=job_id,
        request=request,
        brand=None,
        start_time=time.time(),
    )

    assert state.job_id == job_id
    assert state.request.topic == "AI Agents in production"
    assert len(state.request.platforms) == 2
    assert state.outline == ""
    assert state.outline_approved is False
    assert state.total_cost_usd == 0.0
    assert len(state.steps) == 0


def test_agent_state_add_step():
    """Test the add_step utility on AgentState."""
    job_id = uuid4()
    request = GenerateRequest(topic="Testing steps")
    state = AgentState(job_id=job_id, request=request, start_time=time.time())

    state.add_step(agent="brief_extractor", status="complete", message="Brief parsed successfully")

    assert len(state.steps) == 1
    assert state.steps[0].agent == "brief_extractor"
    assert state.steps[0].status == "complete"
    assert state.steps[0].message == "Brief parsed successfully"


def test_llm_factory_test_mode():
    """Test that LLM factory retrieves the model defined in settings."""
    settings = get_settings()
    settings.default_mode = "test"

    cfg = settings.get_model_config("brief_extractor")
    assert cfg is not None
    assert cfg.model == "gpt-4.1-nano"
