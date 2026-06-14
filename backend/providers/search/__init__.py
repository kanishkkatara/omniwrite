"""
Search providers package for omniwrite.

Exports `get_search_provider()` which selects the best available provider
based on configured API keys: Tavily > Brave > DuckDuckGo (free fallback).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.providers.search.base import SearchProvider
from backend.providers.search.brave_provider import BraveProvider
from backend.providers.search.duckduckgo_provider import DuckDuckGoProvider
from backend.providers.search.tavily_provider import TavilyProvider

if TYPE_CHECKING:
    from backend.core.config import Settings

logger = logging.getLogger(__name__)

__all__ = [
    "SearchProvider",
    "TavilyProvider",
    "BraveProvider",
    "DuckDuckGoProvider",
    "get_search_provider",
]

_PROVIDER_PRIORITY: list[type[SearchProvider]] = [
    TavilyProvider,
    BraveProvider,
    DuckDuckGoProvider,
]


def get_search_provider(settings: "Settings") -> SearchProvider:
    """
    Return the best available search provider given the current settings.

    Priority order: Tavily (best quality) > Brave > DuckDuckGo (free fallback).

    Args:
        settings: Application settings to check for API keys.

    Returns:
        An instantiated SearchProvider ready to use.
    """
    for provider_cls in _PROVIDER_PRIORITY:
        provider = provider_cls()
        if provider.is_available(settings):
            logger.info("Using search provider: %s", provider.name)
            return provider

    # DuckDuckGo should always be available (no key needed), but just in case:
    logger.warning("No search provider available; returning DuckDuckGo as last resort")
    return DuckDuckGoProvider()
