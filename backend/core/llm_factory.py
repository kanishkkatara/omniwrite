"""
LiteLLM-based LLM factory for omniwrite.

Provides a single async entry-point `llm_call` that:
- Resolves the right model via Settings.get_model_config()
- Injects API keys into environment before the call
- Tracks input/output token counts and USD cost
- Falls back gracefully on errors
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import litellm
from litellm import acompletion

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.request import ModelMode

logger = logging.getLogger(__name__)

# Silence litellm's verbose success logs in production
litellm.suppress_debug_info = True


def _inject_api_keys(settings: "Settings") -> None:
    """Set API key environment variables so LiteLLM can pick them up."""
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


async def llm_call(
    messages: list[dict],
    agent_name: str | None = None,
    model_mode: "ModelMode | None" = None,
    temperature_override: float | None = None,
    settings: "Settings | None" = None,
) -> tuple[str, int, int, float]:
    """
    Make an async LLM call via LiteLLM.

    Args:
        messages: OpenAI-format list of message dicts (role/content).
        agent_name: Used to look up the agent-specific model in settings.
        model_mode: Optional override for the model mode.
        temperature_override: Optional temperature override.
        settings: Settings instance (fetched from cache if None).

    Returns:
        Tuple of (response_text, input_tokens, output_tokens, cost_usd).
        On error returns ("", 0, 0, 0.0) so the pipeline doesn't crash.
    """
    from backend.core.config import get_settings

    if settings is None:
        settings = get_settings()

    _inject_api_keys(settings)

    # Resolve model config
    model_cfg = settings.get_model_config(agent_name)

    # If caller passes an explicit model_mode, honour it
    if model_mode is not None:
        mode_str = model_mode.value if hasattr(model_mode, "value") else str(model_mode)
        model_cfg = settings.models.get(mode_str, model_cfg)

    temperature = temperature_override if temperature_override is not None else model_cfg.temperature

    kwargs: dict = {
        "model": model_cfg.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": model_cfg.max_tokens,
        "timeout": model_cfg.timeout,
    }
    if model_cfg.base_url:
        kwargs["base_url"] = model_cfg.base_url

    try:
        logger.debug(
            "llm_call | agent=%s model=%s messages=%d",
            agent_name,
            model_cfg.model,
            len(messages),
        )
        response = await acompletion(**kwargs)

        response_text: str = response.choices[0].message.content or ""

        usage = response.usage or {}
        input_tokens: int = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens: int = getattr(usage, "completion_tokens", 0) or 0

        # Attempt cost calculation
        try:
            cost_usd: float = litellm.completion_cost(completion_response=response)
        except Exception:
            cost_usd = 0.0

        logger.debug(
            "llm_call | done agent=%s in=%d out=%d cost=$%.6f",
            agent_name,
            input_tokens,
            output_tokens,
            cost_usd,
        )
        return response_text, input_tokens, output_tokens, cost_usd

    except litellm.exceptions.AuthenticationError as exc:
        logger.error("llm_call | AuthenticationError for model=%s: %s", model_cfg.model, exc)
        return (
            f"[LLM Error: Authentication failed. Check your API keys. Model: {model_cfg.model}]",
            0,
            0,
            0.0,
        )
    except litellm.exceptions.RateLimitError as exc:
        logger.warning("llm_call | RateLimitError for model=%s: %s", model_cfg.model, exc)
        return "[LLM Error: Rate limit hit. Please retry in a moment.]", 0, 0, 0.0
    except litellm.exceptions.Timeout as exc:
        logger.warning("llm_call | Timeout for model=%s: %s", model_cfg.model, exc)
        return "[LLM Error: Request timed out.]", 0, 0, 0.0
    except Exception as exc:  # noqa: BLE001
        logger.exception("llm_call | Unexpected error for model=%s: %s", model_cfg.model, exc)
        return f"[LLM Error: {exc}]", 0, 0, 0.0
