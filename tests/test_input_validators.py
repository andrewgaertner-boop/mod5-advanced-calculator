"""Tests for REPL input validation."""

import pytest

from app.exceptions import ValidationError
from app.input_validators import parse_number, split_expression


@pytest.mark.parametrize(
    "line, expected",
    [
        ("3 + 4", ("3", "+", "4")),
        ("  -2   *  5 ", ("-2", "*", "5")),
        ("2\troot\t27", ("2", "root", "27")),
        ("1 - -1", ("1", "-", "-1")),
    ],
)
def test_split_expression_accepts_three_tokens(line, expected):
    assert split_expression(line) == expected


@pytest.mark.parametrize("line", ["", "   ", "3 +", "3", "1 2 3 4", "3+4"])
def test_split_expression_rejects_wrong_token_count(line):
    with pytest.raises(ValidationError, match="expected format"):
        split_expression(line)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3", 3.0),
        ("-2.5", -2.5),
        ("  7  ", 7.0),
        ("1e3", 1000.0),
        ("0", 0.0),
    ],
)
def test_parse_number_accepts_finite_numbers(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("text", ["abc", "", "1,000", "3x", "--2"])
def test_parse_number_rejects_non_numbers(text):
    with pytest.raises(ValidationError, match="not a number"):
        parse_number(text)


@pytest.mark.parametrize("text", ["nan", "inf", "-inf", "Infinity"])
def test_parse_number_rejects_non_finite_values(text):
    with pytest.raises(ValidationError, match="must be finite"):
        parse_number(text)
