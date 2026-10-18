from typing import Any, ClassVar

from pydantic import BaseModel

from app.config import get_settings
from app.providers.search import FakeSearchProvider, get_search_provider
from app.tools.calculator import Calculator
from app.tools.registry import ToolRegistry
from app.tools.sources import SourceRegistry
from app.tools.web_search import WebSearch


class _EmptyInput(BaseModel):
    pass


class _CrashingTool:
    name: ClassVar[str] = "crash"
    description: ClassVar[str] = "Always crashes."
    Input: ClassVar[type[BaseModel]] = _EmptyInput

    def run(self, args: _EmptyInput) -> dict[str, Any]:
        raise RuntimeError("database connection lost: password=secret")


def test_definitions_match_anthropic_tool_format() -> None:
    registry = ToolRegistry([Calculator(), WebSearch(FakeSearchProvider(), SourceRegistry())])

    definitions = registry.definitions()

    assert [d["name"] for d in definitions] == ["calculator", "web_search"]
    calc = definitions[0]
    assert set(calc) == {"name", "description", "input_schema"}
    assert calc["input_schema"]["type"] == "object"
    assert calc["input_schema"]["required"] == ["expression"]


def test_calculator_runs_through_registry() -> None:
    outcome = ToolRegistry([Calculator()]).execute("calculator", {"expression": "2 + 2"})

    assert outcome.is_error is False
    assert outcome.content == {"expression": "2 + 2", "result": 4}


def test_unsafe_calculator_input_is_an_error_result() -> None:
    """AC-14 through the registry"""
    outcome = ToolRegistry([Calculator()]).execute(
        "calculator", {"expression": "__import__('os').system('ls')"}
    )

    assert outcome.is_error is True
    assert "error" in outcome.content


def test_unknown_tool_is_an_error_result() -> None:
    outcome = ToolRegistry([Calculator()]).execute("delete_everything", {})

    assert outcome.is_error is True
    assert "Unknown tool" in outcome.content["error"]


def test_missing_input_field_is_an_error_result() -> None:
    outcome = ToolRegistry([Calculator()]).execute("calculator", {})

    assert outcome.is_error is True
    assert "expression" in outcome.content["error"]


def test_unexpected_crash_is_caught_and_details_hidden() -> None:
    """FR-11: a crashing tool never breaks the run, and internals are not leaked."""
    outcome = ToolRegistry([_CrashingTool()]).execute("crash", {})

    assert outcome.is_error is True
    assert outcome.content == {"error": "crash failed unexpectedly."}


def test_search_provider_is_chosen_by_config(monkeypatch) -> None:
    """AC-37: swapping the provider is a config change, no code change."""
    monkeypatch.setenv("SEARCH_PROVIDER", "fake")
    get_settings.cache_clear()
    get_search_provider.cache_clear()
    try:
        assert isinstance(get_search_provider(), FakeSearchProvider)
    finally:
        get_settings.cache_clear()
        get_search_provider.cache_clear()
