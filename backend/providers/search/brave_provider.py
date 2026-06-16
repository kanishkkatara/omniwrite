"""
Brave Search API provider for omniwrite.

Uses httpx to call the Brave Search API (requires BRAVE_SEARCH_API_KEY).
Brave provides high-quality, privacy-focused search results.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from backend.providers.search.base import SearchProvider

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import SearchResult

logger = logging.getLogger(__name__)

_BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveProvider(SearchProvider):
    """Brave Search API provider."""

    name = "brave"
    requires_api_key = True

    def is_available(self, settings: Settings) -> bool:
        return bool(settings.brave_search_api_key)

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        from backend.core.config import get_settings  # noqa: PLC0415
        from backend.models.state import SearchResult  # noqa: PLC0415

        settings = get_settings()
        api_key = settings.brave_search_api_key
        if not api_key:
            logger.warning("BRAVE_SEARCH_API_KEY not set; BraveProvider unavailable")
            return []

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }
        params = {
            "q": query,
            "count": min(num_results, 20),
            "search_lang": "en",
            "result_filter": "web",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(_BRAVE_API_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            results: list[SearchResult] = []
            for item in data.get("web", {}).get("results", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=(item.get("description", "") or "")[:500],
                        source="brave",
                    )
                )
            logger.debug("Brave returned %d results for: %s", len(results), query)
            return results

        except httpx.HTTPStatusError as exc:
            logger.error("Brave API HTTP error %d: %s", exc.response.status_code, exc)
            return []
        except Exception as exc:  # noqa: BLE001
            logger.error("BraveProvider search error: %s", exc)
            return []
