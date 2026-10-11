"""Tests for operation strategies and the operation factory."""

import pytest

from app.exceptions import DivisionByZeroError, OperationError, UnknownOperationError
from app.operations import (
    Add,
    Divide,
    Multiply,
    Operation,
    OperationFactory,
    Power,
    Root,
    Subtract,
)


@pytest.mark.parametrize(
    "key, a, b, expected",
    [
        ("+", 2, 3, 5),
        ("add", 2, 3, 5),
        ("-", 2, 3, -1),
        ("sub", 5, 3, 2),
        ("subtract", 5, 3, 2),
        ("*", 4, 2.5, 10),
        ("mul", 4, 2.5, 10),
        ("multiply", -3, 3, -9),
        ("/", 9, 3, 3),
        ("div", 1, 4, 0.25),
        ("divide", -9, 3, -3),
        ("^", 2, 10, 1024),
        ("**", 2, 3, 8),
        ("pow", 2, 3, 8),
        ("power", 3, 2, 9),
        ("power", 2, -1, 0.5),
        ("power", -2, 3, -8),
        ("root", 9, 2, 3),
        ("root", 16, 4, 2),
        ("root", -8, 3, -2),
        ("root", -27, 3, -3),
        ("root", 8, 1, 8),
        ("root", 0, 5, 0),
    ],
)
def test_factory_creates_strategy_that_computes_expected_result(key, a, b, expected):
    operation = OperationFactory.create(key)
    assert isinstance(operation, Operation)
    assert operation.execute(a, b) == pytest.approx(expected)


@pytest.mark.parametrize(
    "key, expected_type",
    [
        ("+", Add),
        ("-", Subtract),
        ("*", Multiply),
        ("/", Divide),
        ("^", Power),
        ("root", Root),
    ],
)
def test_factory_returns_expected_class(key, expected_type):
    assert type(OperationFactory.create(key)) is expected_type


@pytest.mark.parametrize("key", ["  ADD  ", "Root", "POWER", " ^ "])
def test_factory_is_case_and_whitespace_insensitive(key):
    assert isinstance(OperationFactory.create(key), Operation)


@pytest.mark.parametrize("key", ["%", "", "mod", "sqrt", "x"])
def test_factory_rejects_unknown_keys(key):
    with pytest.raises(UnknownOperationError, match="unknown operation"):
        OperationFactory.create(key)


def test_factory_creates_a_new_instance_each_time():
    assert OperationFactory.create("+") is not OperationFactory.create("+")


def test_symbols_lists_canonical_symbols_in_order():
    assert OperationFactory.symbols() == ("+", "-", "*", "/", "^", "root")


def test_divide_by_zero_raises():
    with pytest.raises(DivisionByZeroError, match="division by zero"):
        Divide().execute(1, 0)


def test_root_degree_zero_raises():
    with pytest.raises(OperationError, match="degree cannot be zero"):
        Root().execute(8, 0)


@pytest.mark.parametrize(
    "a, b",
    [
        (-16, 4),  # even root of a negative number
        (-8, 2.5),  # non-integer degree with a negative base
    ],
)
def test_root_of_negative_number_without_real_result_raises(a, b):
    with pytest.raises(OperationError, match="not a real number"):
        Root().execute(a, b)


def test_root_of_zero_with_negative_degree_raises():
    with pytest.raises(OperationError, match="zero cannot be raised"):
        Root().execute(0, -2)


def test_power_overflow_raises():
    # Floats are used on purpose: integer powers never overflow in Python.
    with pytest.raises(OperationError, match="too large"):
        Power().execute(10.0, 400.0)


def test_power_zero_to_negative_exponent_raises():
    with pytest.raises(OperationError, match="zero cannot be raised"):
        Power().execute(0, -1)


def test_power_negative_base_fractional_exponent_raises():
    with pytest.raises(OperationError, match="not a real number"):
        Power().execute(-8, 0.5)


def test_operation_is_abstract():
    with pytest.raises(TypeError):
        Operation()  # type: ignore[abstract]


def test_symbols_are_unique_across_strategies():
    symbols = OperationFactory.symbols()
    assert len(symbols) == len(set(symbols))
