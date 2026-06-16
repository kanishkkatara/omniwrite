"""
Abstract base class for search providers in omniwrite.

All search providers (Tavily, DuckDuckGo, Brave) implement SearchProvider.
The SearchResult model mirrors backend.models.state.SearchResult for convenience.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.state import SearchResult


class SearchProvider(ABC):
    """Abstract base class for web search providers."""

    name: str = ""
    requires_api_key: bool = True

    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Perform a web search and return a list of SearchResult objects.

        Args:
            query: The search query string.
            num_results: Maximum number of results to return.

        Returns:
            List of SearchResult objects (may be empty on error).
        """

    def is_available(self, settings: Settings) -> bool:
        """
        Check whether this provider can be used with the current settings.

        Override in subclasses to check for required API keys.
        """
        return True

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} name={self.name!r} requires_key={self.requires_api_key}>"
        )
