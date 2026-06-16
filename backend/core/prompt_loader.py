"""
YAML-based prompt loader with Jinja2 templating for omniwrite.

Loads prompt YAML files from backend/core/prompts/ and renders them as
{ system, user } dicts using Jinja2 template substitution.

Usage:
    from backend.core.prompt_loader import loader
    rendered = loader.render("platforms/blog", context={"topic": "AI", ...})
    # → {"system": "...", "user": "..."}
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, StrictUndefined, Template, UndefinedError

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptLoader:
    """Loads and renders YAML-based prompt files with Jinja2 templating."""

    def __init__(self, prompts_dir: Path = _PROMPTS_DIR) -> None:
        self._prompts_dir = prompts_dir
        self._cache: dict[str, dict[str, Any]] = {}
        self._jinja_env = Environment(
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def _load_yaml(self, prompt_name: str) -> dict[str, Any]:
        """Load and cache a YAML prompt file. Returns {} if not found."""
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        # Support both "platforms/blog" and "platforms/blog.yaml"
        name_clean = prompt_name.removesuffix(".yaml")
        path = self._prompts_dir / f"{name_clean}.yaml"

        if not path.exists():
            logger.warning("Prompt file not found: %s", path)
            return {}

        with open(path, encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        self._cache[prompt_name] = raw
        logger.debug("Loaded prompt: %s", path)
        return raw

    def _render_template(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template string with the given context."""
        try:
            tmpl: Template = self._jinja_env.from_string(template_str)
            return tmpl.render(**context)
        except UndefinedError as exc:
            logger.warning(
                "Prompt template variable missing: %s — rendering with relaxed mode", exc
            )
            # Fall back with undefined variables rendered as empty string
            from jinja2 import ChainableUndefined

            fallback_env = Environment(
                undefined=ChainableUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
            )
            tmpl = fallback_env.from_string(template_str)
            return tmpl.render(**context)

    def render(self, prompt_name: str, context: dict[str, Any] | None = None) -> dict[str, str]:
        """
        Load and render a prompt file.

        Args:
            prompt_name: Relative name under prompts/ dir, e.g. "platforms/blog".
            context: Variables for Jinja2 template substitution.

        Returns:
            Dict with keys "system" and "user" containing rendered strings.
            Falls back to empty strings if the file is not found.
        """
        ctx = context or {}
        raw = self._load_yaml(prompt_name)

        if not raw:
            logger.warning("No prompt data for '%s', returning empty prompts", prompt_name)
            return {"system": "", "user": ""}

        system_tmpl: str = raw.get("system", "")
        user_tmpl: str = raw.get("user", "")

        return {
            "system": self._render_template(system_tmpl, ctx),
            "user": self._render_template(user_tmpl, ctx),
        }

    def get_metadata(self, prompt_name: str) -> dict[str, Any]:
        """Return prompt metadata (name, version) without rendering."""
        raw = self._load_yaml(prompt_name)
        return {k: v for k, v in raw.items() if k not in ("system", "user")}

    def invalidate_cache(self) -> None:
        """Clear the in-memory prompt cache (useful for hot-reload in dev)."""
        self._cache.clear()
        logger.debug("Prompt cache cleared")


# ── Singleton instance ────────────────────────────────────────────────────────
loader = PromptLoader()
