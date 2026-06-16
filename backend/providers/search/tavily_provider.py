"""
Tavily search provider for omniwrite.

Uses the official tavily-python async client to perform AI-powered web searches.
Requires a TAVILY_API_KEY.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.providers.search.base import SearchProvider

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import SearchResult

logger = logging.getLogger(__name__)


class TavilyProvider(SearchProvider):
    """Tavily AI-powered search provider."""

    name = "tavily"
    requires_api_key = True

    def is_available(self, settings: Settings) -> bool:
        return bool(settings.tavily_api_key)

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        from backend.models.state import SearchResult  # noqa: PLC0415

        try:
            from tavily import AsyncTavilyClient  # noqa: PLC0415
        except ImportError:
            logger.warning("tavily-python not installed; TavilyProvider unavailable")
            return []

        from backend.core.config import get_settings  # noqa: PLC0415

        settings = get_settings()
        if not settings.tavily_api_key:
            logger.warning("TAVILY_API_KEY not set; TavilyProvider unavailable")
            return []

        try:
            client = AsyncTavilyClient(api_key=settings.tavily_api_key)
            response = await client.search(
                query=query,
                max_results=num_results,
                search_depth="advanced",
                include_answer=False,
            )
            results: list[SearchResult] = []
            for item in response.get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", "")[:500],
                        source="tavily",
                    )
                )
            logger.debug("Tavily returned %d results for: %s", len(results), query)
            return results
        except Exception as exc:  # noqa: BLE001
            logger.error("TavilyProvider search error: %s", exc)
            return []
