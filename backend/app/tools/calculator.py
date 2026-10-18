"""Safe arithmetic for the agent (FR-08).

Claude's output is untrusted, so we never pass it to eval/exec. Instead the expression is
parsed into a syntax tree with `ast`, and we walk the tree ourselves, allowing only
numbers, arithmetic operators, and a short list of math functions. Anything else
(names, attribute access, imports, strings, lambdas...) is rejected before it runs.
"""

import ast
import math
import operator
from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.tools.base import ToolError

MAX_EXPRESSION_LENGTH = 200
MAX_EXPONENT = 100
MAX_RESULT_DIGITS = 300  # refuse results larger than about 10^300

Number = int | float

BINARY_OPS: dict[type[ast.operator], Callable[[Any, Any], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
FUNCTIONS: dict[str, Callable[..., Number]] = {
    "sqrt": math.sqrt,
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
    "log": math.log,  # log(x) is natural log; log(x, base) for other bases
}
CONSTANTS: dict[str, float] = {"pi": math.pi, "e": math.e}


def _check_power(base: Number, exponent: Number) -> None:
    if abs(exponent) > MAX_EXPONENT:
        raise ToolError(f"Exponent too large (limit is {MAX_EXPONENT}).")
    if base != 0 and exponent > 0 and exponent * math.log10(abs(base)) > MAX_RESULT_DIGITS:
        raise ToolError("Result is too large.")


def _eval(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _eval(node.body)

    if isinstance(node, ast.Constant):
        # bool is a subclass of int, so exclude it explicitly.
        if isinstance(node.value, int | float) and not isinstance(node.value, bool):
            return node.value
        raise ToolError(f"Only numbers are allowed, not {node.value!r}.")

    if isinstance(node, ast.BinOp):
        op = BINARY_OPS.get(type(node.op))
        if op is None:
            hint = " Use ** for powers." if isinstance(node.op, ast.BitXor) else ""
            raise ToolError(f"Operator not allowed.{hint}")
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow):
            _check_power(left, right)
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        unary = UNARY_OPS.get(type(node.op))
        if unary is None:
            raise ToolError("Operator not allowed.")
        return unary(_eval(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            raise ToolError(f"Only these functions are allowed: {', '.join(FUNCTIONS)}.")
        if node.keywords:
            raise ToolError("Keyword arguments are not allowed.")
        return FUNCTIONS[node.func.id](*(_eval(arg) for arg in node.args))

    if isinstance(node, ast.Name):
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise ToolError(f"Unknown name {node.id!r}.")

    raise ToolError(f"{type(node).__name__} is not allowed in an expression.")


def evaluate(expression: str) -> Number:
    """Evaluate an arithmetic expression safely. Raises ToolError for anything else."""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ToolError(f"Expression is longer than {MAX_EXPRESSION_LENGTH} characters.")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ToolError("Expression is not valid arithmetic.") from exc
    try:
        result = _eval(tree)
    except ZeroDivisionError as exc:
        raise ToolError("Division by zero.") from exc
    except (ValueError, TypeError, OverflowError) as exc:  # e.g. sqrt(-1), min()
        raise ToolError(f"Math error: {exc}.") from exc
    if not isinstance(result, int | float):  # e.g. (-8) ** 0.5 gives a complex number
        raise ToolError("Result is not a real number.")
    if isinstance(result, int) and abs(result) > 10**MAX_RESULT_DIGITS:
        raise ToolError("Result is too large.")
    if isinstance(result, float):
        if math.isnan(result) or math.isinf(result):
            raise ToolError("Result is not a finite number.")
        result = float(f"{result:.10g}")  # 10 significant digits, hides 0.1+0.2 noise
    return result


class CalculatorInput(BaseModel):
    expression: str = Field(
        min_length=1,
        max_length=MAX_EXPRESSION_LENGTH,
        description="Arithmetic expression, e.g. '(5.1 - 4.2) / 4.2 * 100'.",
    )


class Calculator:
    name: ClassVar[str] = "calculator"
    description: ClassVar[str] = (
        "Evaluate an arithmetic expression exactly. Use it for ANY math instead of doing it "
        "yourself. Supports + - * / // % **, parentheses, the constants pi and e, and the "
        "functions sqrt, round, abs, min, max, log (log(x) is natural log; log(x, 10) is "
        "base 10)."
    )
    Input: ClassVar[type[BaseModel]] = CalculatorInput

    def run(self, args: CalculatorInput) -> dict[str, Any]:
        return {"expression": args.expression, "result": evaluate(args.expression)}
