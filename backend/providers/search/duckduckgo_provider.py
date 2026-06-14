"""
DuckDuckGo search provider for omniwrite.

Uses duckduckgo_search (free, no API key required) as a fallback provider.
Runs synchronous DDG calls in a thread executor to remain async-compatible.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from backend.providers.search.base import SearchProvider

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search provider — free, no API key required."""

    name = "duckduckgo"
    requires_api_key = False

    def is_available(self, settings: "Settings") -> bool:  # noqa: ARG002
        try:
            import duckduckgo_search  # noqa: F401

            return True
        except ImportError:
            return False

    async def search(self, query: str, num_results: int = 5) -> list["SearchResult"]:
        from backend.models.state import SearchResult  # noqa: PLC0415

        try:
            from duckduckgo_search import DDGS  # noqa: PLC0415
        except ImportError:
            logger.warning("duckduckgo-search not installed; DuckDuckGoProvider unavailable")
            return []

        def _sync_search() -> list[dict]:
            try:
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=num_results))
            except Exception as exc:  # noqa: BLE001
                logger.error("DuckDuckGo search error: %s", exc)
                return []

        try:
            loop = asyncio.get_event_loop()
            raw_results: list[dict] = await loop.run_in_executor(None, _sync_search)
            results: list[SearchResult] = []
            for item in raw_results:
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", ""),
                        snippet=item.get("body", "")[:500],
                        source="duckduckgo",
                    )
                )
            logger.debug("DuckDuckGo returned %d results for: %s", len(results), query)
            return results
        except Exception as exc:  # noqa: BLE001
            logger.error("DuckDuckGoProvider async wrapper error: %s", exc)
            return []
