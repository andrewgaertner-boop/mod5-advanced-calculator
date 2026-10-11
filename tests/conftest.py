"""Shared pytest fixtures."""

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


@pytest.fixture
def config(tmp_path):
    """A configuration whose history file lives in a temporary folder."""
    return CalculatorConfig(history_file=tmp_path / "history.csv", auto_save=False)


@pytest.fixture
def calculator(config):
    """A calculator with no observers and an empty history."""
    return Calculator(config)
