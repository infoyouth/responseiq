from typing import List, Optional, Type

from .base import BaseParser


class ParserRegistry:
    _parsers: List[BaseParser] = []

    @classmethod
    def register(cls, parser_cls: Type[BaseParser]) -> None:
        """Register a new parser class (instantiates it)."""
        instance = parser_cls()
        cls._parsers.append(instance)

    @classmethod
    def get_parsers(cls) -> List[BaseParser]:
        """Return list of registered parser instances."""
        return cls._parsers

    @classmethod
    def find_parser(cls, log_line: str) -> Optional[BaseParser]:
        """Find the first parser that can handle the log line."""
        for parser in cls._parsers:
            if parser.can_handle(log_line):
                return parser
        return None


# Global registry accessor if needed, or just use class methods
registry = ParserRegistry
