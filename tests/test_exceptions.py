"""Tests for the exception hierarchy."""

import pytest

from app import exceptions as exc

ALL_ERRORS = [
    exc.CalculatorError,
    exc.ValidationError,
    exc.UnknownOperationError,
    exc.OperationError,
    exc.DivisionByZeroError,
    exc.ConfigurationError,
    exc.HistoryError,
    exc.MementoError,
]


@pytest.mark.parametrize(
    "error_cls, parent",
    [
        (exc.ValidationError, exc.CalculatorError),
        (exc.UnknownOperationError, exc.ValidationError),
        (exc.OperationError, exc.CalculatorError),
        (exc.DivisionByZeroError, exc.OperationError),
        (exc.ConfigurationError, exc.CalculatorError),
        (exc.HistoryError, exc.CalculatorError),
        (exc.MementoError, exc.CalculatorError),
    ],
)
def test_error_hierarchy(error_cls, parent):
    assert issubclass(error_cls, parent)


@pytest.mark.parametrize("error_cls", ALL_ERRORS)
def test_errors_keep_their_message(error_cls):
    with pytest.raises(exc.CalculatorError, match="something broke"):
        raise error_cls("something broke")


@pytest.mark.parametrize("error_cls", ALL_ERRORS)
def test_errors_are_exceptions(error_cls):
    assert issubclass(error_cls, Exception)
