from typing import Any, ClassVar, Protocol

from pydantic import BaseModel


class ToolError(Exception):
    """An expected failure with a message that is safe to show Claude and the user."""


class Tool(Protocol):
    """One tool Claude can ask for. Every tool is read-only (NFR-06)."""

    name: ClassVar[str]
    description: ClassVar[str]
    Input: ClassVar[type[BaseModel]]

    def run(self, args: Any) -> dict[str, Any]:
        """Takes a validated `Input` instance and returns a JSON-serialisable result."""
        ...
