"""
Abstract base class for all platform plugins in omniwrite.

Every platform plugin (Blog, Reddit, LinkedIn, etc.) must subclass
PlatformPlugin and implement `generate` and `get_system_prompt`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.config import Settings
    from backend.models.brand import BrandProfile
    from backend.models.state import AgentState


class PlatformPlugin(ABC):
    """Abstract base class for a omniwriteeration platform plugin."""

    # ── Class-level metadata (subclasses must set these) ─────────────────────
    name: str = ""
    display_name: str = ""
    icon: str = "📄"
    max_words: int = 1000
    supports_publish: bool = False

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    async def generate(self, state: "AgentState", settings: "Settings") -> str:
        """
        Generate platform content for the given agent state.

        Args:
            state: The current LangGraph AgentState.
            settings: Application settings.

        Returns:
            The generated content string.
        """

    @abstractmethod
    def get_system_prompt(self, brand: "BrandProfile | None") -> str:
        """
        Build a system prompt incorporating the brand profile (if any).

        Args:
            brand: Optional BrandProfile for voice/tone context.

        Returns:
            System prompt string.
        """

    # ── Concrete helpers ──────────────────────────────────────────────────────

    def validate_content(self, content: str) -> bool:
        """
        Basic validation: ensures content is non-empty and within word limits.

        Returns True if content is valid, False otherwise.
        """
        if not content or not content.strip():
            return False
        word_count = len(content.split())
        # Allow up to 50% over max_words (LLM sometimes overshoots)
        if word_count > self.max_words * 1.5:
            return False
        return True

    def word_count(self, content: str) -> int:
        """Return the word count of content."""
        return len(content.split()) if content else 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} max_words={self.max_words}>"
