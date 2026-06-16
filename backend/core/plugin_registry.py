"""
Plugin registry for omniwrite platform plugins.

Provides a singleton PluginRegistry that:
- Stores registered PlatformPlugin instances by name
- Discovers plugins by scanning directories for PlatformPlugin subclasses
- Supports get / list / register operations

Usage:
    from backend.core.plugin_registry import registry
    registry.discover([Path("backend/plugins")])
    plugin = registry.get("blog")
"""

from __future__ import annotations

import importlib.util
import inspect
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.plugins.base import PlatformPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry of available platform plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, PlatformPlugin] = {}

    def register(self, plugin: PlatformPlugin) -> None:
        """Register a plugin instance under its name."""
        self._plugins[plugin.name] = plugin
        logger.debug("Registered plugin: %s (%s)", plugin.name, plugin.display_name)

    def get(self, name: str) -> PlatformPlugin | None:
        """Return the plugin with the given name, or None if not found."""
        return self._plugins.get(name)

    def list_plugins(self) -> list[PlatformPlugin]:
        """Return all registered plugins."""
        return list(self._plugins.values())

    def discover(self, plugin_dirs: list[Path]) -> None:
        """
        Scan directories for Python files containing PlatformPlugin subclasses
        and register any found instances.
        """
        # Import lazily to avoid circular imports at module load time
        from backend.plugins.base import PlatformPlugin  # noqa: PLC0415

        for directory in plugin_dirs:
            if not directory.exists():
                logger.warning("Plugin directory not found: %s", directory)
                continue

            for py_file in sorted(directory.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                try:
                    module_name = f"_plugin_discovery.{py_file.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore[attr-defined]

                    for _name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, PlatformPlugin)
                            and obj is not PlatformPlugin
                            and not inspect.isabstract(obj)
                        ):
                            try:
                                instance = obj()
                                self.register(instance)
                            except Exception as exc:  # noqa: BLE001
                                logger.warning(
                                    "Could not instantiate plugin %s: %s", obj.__name__, exc
                                )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Error scanning plugin file %s: %s", py_file, exc)

        logger.info(
            "Plugin discovery complete. Registered: %s",
            [p.name for p in self.list_plugins()],
        )


# ── Singleton instance ────────────────────────────────────────────────────────
registry = PluginRegistry()
