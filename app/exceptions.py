"""Exception hierarchy for the calculator.

Every error the application raises on purpose derives from ``CalculatorError``,
so the REPL can catch one base class and report any failure gracefully.
"""


class CalculatorError(Exception):
    """Base class for all calculator errors."""


class ValidationError(CalculatorError):
    """Raised when user input is malformed."""


class UnknownOperationError(ValidationError):
    """Raised when an operator symbol or name is not recognised."""


class OperationError(CalculatorError):
    """Raised when an arithmetic operation cannot produce a valid result."""


class DivisionByZeroError(OperationError):
    """Raised when a division has a zero divisor."""


class ConfigurationError(CalculatorError):
    """Raised when a configuration value is invalid."""


class HistoryError(CalculatorError):
    """Raised when history cannot be read from or written to storage."""


class MementoError(CalculatorError):
    """Raised when there is no state to undo or redo."""
