# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 ResponseIQ contributors
"""Plugin auto-discovery and registry.

Scans the ``plugins/`` directory at startup, imports every module that
subclasses ``BasePlugin``, and registers it so the scan/fix pipeline can
dispatch log lines to the right language-specific parser automatically.
"""

import importlib
import os
import pkgutil
from typing import Dict, Type

from responseiq.plugins.base import BasePlugin

PLUGIN_PATH = os.path.join(os.path.dirname(__file__), "plugins")


class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, Type[BasePlugin]] = {}
        self._discover_plugins()

    def _discover_plugins(self):
        for _, name, ispkg in pkgutil.iter_modules([PLUGIN_PATH]):
            if not ispkg and name != "base":
                module = importlib.import_module(f"responseiq.plugins.{name}")
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
                        self.plugins[name] = obj

    def get_plugin(self, name: str) -> Type[BasePlugin]:
        return self.plugins[name]

    def list_plugins(self):
        return list(self.plugins.keys())
