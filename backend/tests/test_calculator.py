import pytest

from app.tools.base import ToolError
from app.tools.calculator import evaluate


def test_percentage_growth_example() -> None:
    """AC-13"""
    assert round(evaluate("(5.1 - 4.2) / 4.2 * 100"), 2) == 21.43


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 2 * 3", 7),
        ("(1 + 2) * 3", 9),
        ("7 / 2", 3.5),
        ("7 // 2", 3),
        ("7 % 3", 1),
        ("2 ** 10", 1024),
        ("-3 + +5", 2),
        ("0.1 + 0.2", 0.3),
        ("sqrt(16)", 4.0),
        ("round(3.14159, 2)", 3.14),
        ("abs(-4)", 4),
        ("min(3, 1, 2) + max(3, 1, 2)", 4),
        ("log(100, 10)", 2.0),
        ("round(pi, 4)", 3.1416),
        ("1_000 * 1.5", 1500.0),
    ],
)
def test_allowed_arithmetic(expression: str, expected: float) -> None:
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('ls')",  # AC-14: code injection
        "open('/etc/passwd').read()",
        "().__class__.__bases__[0].__subclasses__()",
        "(lambda: 1)()",
        "x + 1",
        "'a' * 3",
        "True + 1",
        "[1, 2, 3]",
        "1 if 2 else 3",
        "sqrt(x=4)",
    ],
)
def test_anything_but_arithmetic_is_rejected(expression: str) -> None:
    with pytest.raises(ToolError):
        evaluate(expression)


def test_division_by_zero_is_an_error() -> None:
    """AC-14"""
    with pytest.raises(ToolError, match="Division by zero"):
        evaluate("1/0")


@pytest.mark.parametrize("expression", ["9 ** 9 ** 9", "10 ** 1000", "(9 ** 99) ** 99"])
def test_huge_powers_are_refused_quickly(expression: str) -> None:
    with pytest.raises(ToolError):
        evaluate(expression)


@pytest.mark.parametrize("expression", ["sqrt(-1)", "log(0)", "(-8) ** 0.5", "min()"])
def test_math_errors_become_tool_errors(expression: str) -> None:
    with pytest.raises(ToolError):
        evaluate(expression)


def test_caret_gives_a_helpful_hint() -> None:
    with pytest.raises(ToolError, match=r"\*\*"):
        evaluate("2 ^ 3")


def test_long_and_invalid_expressions_are_rejected() -> None:
    with pytest.raises(ToolError, match="longer than"):
        evaluate("1+" * 150 + "1")
    with pytest.raises(ToolError, match="not valid"):
        evaluate("2 +* 3")
