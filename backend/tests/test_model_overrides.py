"""
Unit tests for request-level custom model settings overrides.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from backend.models.request import GenerateRequest, ModelMode, Platform
from backend.services.job_service import job_service
from backend.core.config import get_settings


@pytest.mark.asyncio
@patch("backend.services.job_service.job_store")
@patch("backend.agents.graph.create_graph")
async def test_run_job_model_overrides(mock_create_graph, mock_job_store):
    """Test that custom test/prod models in request override settings copy without polluting singleton."""
    # Get baseline singleton settings
    baseline_settings = get_settings()
    original_test_model = baseline_settings.models["test"].model
    original_prod_model = baseline_settings.models["production"].model

    # Set up mock job store
    mock_job_store.update_job_status = AsyncMock()

    # Create request with overrides
    request = GenerateRequest(
        topic="Custom model overrides test",
        platforms=[Platform.BLOG],
        test_model="openai/gpt-4o-custom-test",
        production_model="anthropic/claude-sonnet-custom-prod",
    )

    # We mock graph.astream to complete instantly
    mock_graph = MagicMock()
    async def empty_stream(*args, **kwargs):
        # yields nothing
        if False:
            yield None
    mock_graph.astream = empty_stream
    mock_create_graph.return_value = mock_graph

    # Run the job service runner
    await job_service.run_job(
        job_id="00000000-0000-0000-0000-000000000000",
        request=request,
        brand=None,
    )

    # Verify create_graph was called with settings containing the custom overrides
    mock_create_graph.assert_called_once()
    passed_settings = mock_create_graph.call_args[0][0]

    assert passed_settings.models["test"].model == "openai/gpt-4o-custom-test"
    assert passed_settings.models["production"].model == "anthropic/claude-sonnet-custom-prod"

    # Verify that the cached singleton settings were NOT modified
    current_settings = get_settings()
    assert current_settings.models["test"].model == original_test_model
    assert current_settings.models["production"].model == original_prod_model


@pytest.mark.asyncio
@patch("backend.services.job_service.job_store")
@patch("backend.core.llm_factory.acompletion")
async def test_regenerate_platform_model_overrides(mock_acompletion, mock_job_store):
    """Test that custom test/prod models are loaded from request json and applied during platform regeneration."""
    # Mock return value of acompletion
    mock_response = AsyncMock()
    mock_response.choices = [
        AsyncMock(message=AsyncMock(content="Hello response content"))
    ]
    mock_response.usage = AsyncMock(prompt_tokens=15, completion_tokens=25)
    mock_acompletion.return_value = mock_response

    # Define a mock job with custom model request data
    request_data = {
        "topic": "Regeneration model test",
        "platforms": ["blog"],
        "test_model": "openai/gpt-4o-mini",
        "production_model": "anthropic/claude-3-5-sonnet",
    }
    
    mock_job = MagicMock()
    mock_job.request_json = json.dumps(request_data)
    mock_job.state_json = json.dumps({
        "job_id": "00000000-0000-0000-0000-000000000000",
        "outputs": {},
    })
    
    mock_job_store.get_job = AsyncMock(return_value=mock_job)
    mock_job_store.update_job_outputs = AsyncMock()

    # Trigger regeneration
    await job_service.regenerate_platform(
        job_id="00000000-0000-0000-0000-000000000000",
        platform="blog",
    )

    # Yield to event loop to allow the background task (_regen) to run and finish
    await asyncio.sleep(0.2)

    # Verify update_job_outputs was called with regenerated output
    mock_job_store.update_job_outputs.assert_called_once()
    
    # Check that settings passed down to LiteLLM contained the custom test model override
    mock_acompletion.assert_called()
    called_model = mock_acompletion.call_args[1].get("model")
    assert called_model == "openai/gpt-4o-mini"
