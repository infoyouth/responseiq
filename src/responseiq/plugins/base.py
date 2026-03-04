"""src/responseiq/plugins/base.py

P5.2: Plugin SDK base interface.

Every log-parser plugin must subclass ``BasePlugin``, declare a ``metadata``
class attribute of type ``PluginMetadata``, and implement both ``can_handle``
and ``run``.

Discovery
─────────
``PluginRegistry`` (``plugin_registry.py``) auto-discovers all subclasses that
live in the ``src/responseiq/plugins/`` directory via ``pkgutil.iter_modules``.

Writing a custom plugin
───────────────────────
    from responseiq.plugins.base import BasePlugin, PluginMetadata

    class MyParser(BasePlugin):
        metadata = PluginMetadata(
            name="my_parser",
            version="1.0.0",
            author="you@example.com",
            log_format="my-framework",
            description="Parses MyFramework error logs.",
        )

        @classmethod
        def can_handle(cls, log_text: str) -> bool:
            return "MyFramework" in log_text

        def run(self, agent_state: dict) -> dict:
            # Extract relevant info and return delta
            return {"parsed_framework": "my-framework"}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PluginMetadata:
    """Declarative metadata attached to every plugin class."""

    name: str
    version: str
    author: str
    log_format: str
    description: str = ""


class BasePlugin(ABC):
    """Abstract base class for all ResponseIQ log-parser plugins."""

    #: Subclasses MUST define this class attribute.
    metadata: PluginMetadata

    @classmethod
    def can_handle(cls, log_text: str) -> bool:  # noqa: ARG003
        """Return ``True`` if this plugin can meaningfully parse *log_text*.

        Override in each concrete plugin.  The default implementation returns
        ``False`` so unimplemented plugins are never auto-selected.
        """
        return False

    @abstractmethod
    def run(self, agent_state: dict) -> dict:
        """Run the plugin with the provided agent state.

        Returns a *delta* dict that is merged into the agent state by the
        caller.  Only include keys that the plugin wishes to set or update.
        """
