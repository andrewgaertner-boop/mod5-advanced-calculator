"""Arithmetic operations.

Each operation is a *Strategy*: a class implementing ``Operation.execute``.
``OperationFactory`` is the *Factory* that builds the right strategy from the
symbol or name the user typed.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from app.exceptions import DivisionByZeroError, OperationError, UnknownOperationError


def _real_pow(base: float, exponent: float) -> float:
    """Raise ``base`` to ``exponent`` and make sure the result is real.

    EAFP: the power is attempted and Python's failure modes are translated
    into ``OperationError``.
    """
    try:
        result = base**exponent
    except OverflowError as exc:
        raise OperationError("result is too large to represent") from exc
    except ZeroDivisionError as exc:
        raise OperationError("zero cannot be raised to a negative power") from exc
    if isinstance(result, complex):  # e.g. (-8) ** 0.5 returns a complex number
        raise OperationError("result is not a real number")
    return result


def _is_odd_integer(value: float) -> bool:
    """Return True when ``value`` is a whole number with an odd magnitude."""
    return value.is_integer() and int(value) % 2 == 1


class Operation(ABC):
    """Strategy interface for a binary arithmetic operation."""

    symbol: ClassVar[str]
    names: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def execute(self, a: float, b: float) -> float:
        """Return the result of applying the operation to ``a`` and ``b``."""


class Add(Operation):
    """Addition: ``a + b``."""

    symbol = "+"
    names = ("add",)

    def execute(self, a: float, b: float) -> float:
        return a + b


class Subtract(Operation):
    """Subtraction: ``a - b``."""

    symbol = "-"
    names = ("sub", "subtract")

    def execute(self, a: float, b: float) -> float:
        return a - b


class Multiply(Operation):
    """Multiplication: ``a * b``."""

    symbol = "*"
    names = ("mul", "multiply")

    def execute(self, a: float, b: float) -> float:
        return a * b


class Divide(Operation):
    """Division: ``a / b``. Raises ``DivisionByZeroError`` when ``b`` is zero."""

    symbol = "/"
    names = ("div", "divide")

    def execute(self, a: float, b: float) -> float:
        if b == 0:  # LBYL: check the divisor before dividing
            raise DivisionByZeroError("division by zero")
        return a / b


class Power(Operation):
    """Exponentiation: ``a ^ b``."""

    symbol = "^"
    names = ("**", "pow", "power")

    def execute(self, a: float, b: float) -> float:
        return _real_pow(a, b)


class Root(Operation):
    """Nth root: ``a root b`` is the ``b``-th root of ``a``.

    Negative bases are allowed only when the degree is an odd whole number.
    """

    symbol = "root"

    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("root degree cannot be zero")
        if a < 0 and _is_odd_integer(b):
            return -_real_pow(-a, 1 / b)
        return _real_pow(a, 1 / b)


_OPERATION_TYPES: tuple[type[Operation], ...] = (Add, Subtract, Multiply, Divide, Power, Root)

# Lookup table: every symbol and alias (lower-case) maps to its strategy class.
_REGISTRY: dict[str, type[Operation]] = {
    key: op_type for op_type in _OPERATION_TYPES for key in (op_type.symbol, *op_type.names)
}


class OperationFactory:
    """Factory that creates operation strategies from user input."""

    @staticmethod
    def create(key: str) -> Operation:
        """Return a new operation for ``key``, a symbol or name (case-insensitive)."""
        normalised = key.strip().lower()
        if normalised not in _REGISTRY:  # LBYL: confirm the key exists before indexing
            raise UnknownOperationError(f"unknown operation: {key!r}")
        return _REGISTRY[normalised]()

    @staticmethod
    def symbols() -> tuple[str, ...]:
        """Return the canonical symbol of every supported operation."""
        return tuple(op_type.symbol for op_type in _OPERATION_TYPES)
