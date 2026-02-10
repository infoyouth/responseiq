from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseParser(ABC):
    """Abstract base class for all log parsers."""

    @abstractmethod
    def can_handle(self, log_line: str) -> bool:
        """Return True if this parser can handle the given log line."""
        pass

    @abstractmethod
    def parse(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse the log line and return structured data.
        Returns a dict with implementation-specific fields, or None if parsing fails.
        """
        pass
