import tomllib
from pathlib import Path
from typing import Set

from responseiq.utils.logger import logger

# Default "Safe" ignores so users don't accidentaly scan the world
DEFAULT_IGNORED_EXTENSIONS = {
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".toml",
    ".pyc",
    ".pyo",
    ".lock",
    ".whl",
    ".png",
    ".jpg",
    ".gif",
    ".css",
    ".map",
    # Source code (exclude from generic directory scans unless explicitly targeted)
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".html",
    ".scss",
    ".sh",
}

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "system",
    "site-packages",
    "tests",
    "test",
    "docs",
    "fixtures",
}


class ResponseIQConfig:
    def __init__(self, root_path: Path = Path(".")):
        self.root_path = root_path
        self.ignored_extensions: Set[str] = DEFAULT_IGNORED_EXTENSIONS.copy()
        self.ignored_dirs: Set[str] = DEFAULT_IGNORED_DIRS.copy()

        # Load from file
        self._load_config()

    def _load_config(self):
        """Attempts to load configuration from pyproject.toml"""
        config_path = self.root_path / "pyproject.toml"
        if not config_path.exists():
            return

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            tool_config = data.get("tool", {}).get("responseiq", {})

            if not tool_config:
                return

            logger.debug(f"Loading configuration from {config_path}")

            # Override or Append?
            # Strategy: If user defines list, we use theirs + essential system ignores?
            # Or just replace? standard behavior is usually replace if defined.

            if "ignore_extensions" in tool_config:
                self.ignored_extensions = set(tool_config["ignore_extensions"])
                logger.debug(f"Loaded {len(self.ignored_extensions)} ignore_extensions patterns")

            if "ignore_dirs" in tool_config:
                self.ignored_dirs = set(tool_config["ignore_dirs"])
                logger.debug(f"Loaded {len(self.ignored_dirs)} ignore_dirs patterns")

        except Exception as e:
            logger.warning(f"Failed to parse configuration from {config_path}: {e}")

    def is_ignored(self, file_path: Path) -> bool:
        """Check if a file or directory should be ignored"""
        if file_path.name.startswith("."):
            return True

        # Directory check
        if file_path.is_dir():
            return file_path.name in self.ignored_dirs

        # SMART HEURISTIC: "Log Folder Exception"
        # If the file is inside a directory named 'log' or 'logs', we relax the checks
        # to allow .json, .yaml, .xml which are often use for structured logs.
        # We still block binaries.
        is_in_log_folder = any(p.lower() in ["log", "logs"] for p in file_path.parts)

        suffix = file_path.suffix.lower()

        if is_in_log_folder:
            # If in logs/, ONLY block actual binaries or irrelevant assets
            BINARY_EXTENSIONS = {
                ".pyc",
                ".pyo",
                ".lock",
                ".whl",
                ".png",
                ".jpg",
                ".gif",
                ".css",
                ".map",
                ".exe",
                ".bin",
                ".dll",
                ".so",
            }
            return suffix in BINARY_EXTENSIONS

        # Normal Strict Check
        return suffix in self.ignored_extensions or file_path.name in self.ignored_dirs


def load_config(path: Path = Path(".")) -> ResponseIQConfig:
    return ResponseIQConfig(path)
