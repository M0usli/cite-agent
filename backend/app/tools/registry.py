import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.tools.base import Tool, ToolError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolOutcome:
    """What gets sent back to Claude as a tool_result block."""

    content: dict[str, Any]
    is_error: bool


class ToolRegistry:
    """The tools available in one agent run, plus safe execution (FR-11)."""

    def __init__(self, tools: Sequence[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def definitions(self) -> list[dict[str, Any]]:
        """Tool definitions in the shape the Anthropic Messages API expects."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.Input.model_json_schema(),
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, raw_input: dict[str, Any]) -> ToolOutcome:
        """Run a tool. Never raises: every failure becomes an error result for Claude."""
        tool = self._tools.get(name)
        if tool is None:
            return ToolOutcome({"error": f"Unknown tool {name!r}."}, is_error=True)
        try:
            args = tool.Input.model_validate(raw_input)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(p) for p in e['loc']) or 'input'}: {e['msg']}" for e in exc.errors()
            )
            return ToolOutcome({"error": f"Invalid input: {problems}"}, is_error=True)
        try:
            return ToolOutcome(tool.run(args), is_error=False)
        except ToolError as exc:
            return ToolOutcome({"error": str(exc)}, is_error=True)
        except Exception:
            logger.exception("Tool %s crashed", name)
            return ToolOutcome({"error": f"{name} failed unexpectedly."}, is_error=True)
