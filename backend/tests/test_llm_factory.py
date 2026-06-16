"""
Unit tests for LiteLLM factory and key injections.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch
import pytest

from backend.core.config import Settings
from backend.core.llm_factory import llm_call, _inject_api_keys
from backend.models.request import ModelMode


def test_inject_api_keys():
    """Test environment variable injection from settings."""
    # We pass variables matching the aliases (case-sensitive matching env)
    settings = Settings(
        OPENAI_API_KEY="mock-openai-key",
        ANTHROPIC_API_KEY="mock-anthropic-key",
    )

    # Save original values
    orig_openai = os.environ.get("OPENAI_API_KEY")
    orig_anthropic = os.environ.get("ANTHROPIC_API_KEY")

    try:
        _inject_api_keys(settings)
        assert os.environ["OPENAI_API_KEY"] == "mock-openai-key"
        assert os.environ["ANTHROPIC_API_KEY"] == "mock-anthropic-key"
    finally:
        # Restore environment
        if orig_openai is not None:
            os.environ["OPENAI_API_KEY"] = orig_openai
        else:
            os.environ.pop("OPENAI_API_KEY", None)

        if orig_anthropic is not None:
            os.environ["ANTHROPIC_API_KEY"] = orig_anthropic
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.mark.asyncio
@patch("backend.core.llm_factory.acompletion")
async def test_llm_call_success(mock_acompletion):
    """Test successful LLM calls resolve correctly and report costs."""
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(message=AsyncMock(content="Hello response content"))
    ]
    mock_response.usage = AsyncMock(prompt_tokens=15, completion_tokens=25)
    mock_acompletion.return_value = mock_response

    messages = [{"role": "user", "content": "hi"}]
    res, in_tok, out_tok, cost = await llm_call(
        messages=messages,
        model_mode=ModelMode.TEST,
    )

    assert res == "Hello response content"
    assert in_tok == 15
    assert out_tok == 25
    # Verification that costing computes a float greater than or equal to 0.0
    assert isinstance(cost, float)
    assert cost >= 0.0


@pytest.mark.asyncio
@patch("backend.core.llm_factory.acompletion", side_effect=Exception("LiteLLM mock connection error"))
async def test_llm_call_failure_fallback(mock_acompletion):
    """Test that LLM factory falls back gracefully on LiteLLM connection failures."""
    messages = [{"role": "user", "content": "fail test"}]
    res, in_tok, out_tok, cost = await llm_call(
        messages=messages,
        model_mode=ModelMode.TEST,
    )

    assert "[LLM Error:" in res
    assert "LiteLLM mock connection error" in res
    assert in_tok == 0
    assert out_tok == 0
    assert cost == 0.0
