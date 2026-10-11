"""The ``Calculation`` value object: one completed arithmetic operation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.operations import OperationFactory


@dataclass(frozen=True)
class Calculation:
    """An immutable record of ``operand_a operator operand_b = result``."""

    operand_a: float
    operator: str
    operand_b: float
    result: float
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def perform(cls, operand_a: float, operator: str, operand_b: float) -> "Calculation":
        """Build the operation strategy via the factory, run it, and record the outcome."""
        operation = OperationFactory.create(operator)
        result = operation.execute(operand_a, operand_b)
        return cls(operand_a, operation.symbol, operand_b, result)

    def to_record(self) -> dict[str, Any]:
        """Return the calculation as a flat dict matching the history columns."""
        return {
            "timestamp": self.timestamp.isoformat(timespec="seconds"),
            "operand_a": self.operand_a,
            "operator": self.operator,
            "operand_b": self.operand_b,
            "result": self.result,
        }

    def describe(self, precision: int) -> str:
        """Return a display string such as ``3 + 4 = 7``."""
        return (
            f"{self.operand_a:g} {self.operator} {self.operand_b:g} "
            f"= {self.result:.{precision}g}"
        )
