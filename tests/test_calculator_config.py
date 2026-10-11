"""Tests for environment-based configuration and its validation."""

from pathlib import Path

import pytest

import app.calculator_config as config_module
from app.calculator_config import CalculatorConfig, DEFAULT_HISTORY_FILE
from app.exceptions import ConfigurationError


def test_empty_environment_gives_defaults():
    assert CalculatorConfig.from_env({}) == CalculatorConfig()


def test_defaults_are_sensible():
    config = CalculatorConfig()
    assert config.history_file == Path(DEFAULT_HISTORY_FILE)
    assert config.auto_save is True
    assert config.precision == 6
    assert config.log_level == "WARNING"


@pytest.mark.parametrize(
    "env, expected",
    [
        ({"CALC_HISTORY_FILE": "  my/history.csv  "}, {"history_file": Path("my/history.csv")}),
        ({"CALC_AUTO_SAVE": "false"}, {"auto_save": False}),
        ({"CALC_AUTO_SAVE": "OFF"}, {"auto_save": False}),
        ({"CALC_AUTO_SAVE": "0"}, {"auto_save": False}),
        ({"CALC_AUTO_SAVE": "Yes"}, {"auto_save": True}),
        ({"CALC_AUTO_SAVE": "1"}, {"auto_save": True}),
        ({"CALC_PRECISION": "3"}, {"precision": 3}),
        ({"CALC_PRECISION": " 0 "}, {"precision": 0}),
        ({"CALC_PRECISION": "15"}, {"precision": 15}),
        ({"CALC_LOG_LEVEL": "debug"}, {"log_level": "DEBUG"}),
        ({"CALC_LOG_LEVEL": "error"}, {"log_level": "ERROR"}),
    ],
)
def test_valid_values_are_parsed(env, expected):
    config = CalculatorConfig.from_env(env)
    for field, value in expected.items():
        assert getattr(config, field) == value


@pytest.mark.parametrize(
    "env",
    [
        {"CALC_HISTORY_FILE": "   "},
        {"CALC_AUTO_SAVE": ""},
        {"CALC_PRECISION": "  "},
        {"CALC_LOG_LEVEL": ""},
    ],
)
def test_blank_values_fall_back_to_defaults(env):
    assert CalculatorConfig.from_env(env) == CalculatorConfig()


@pytest.mark.parametrize(
    "env, message",
    [
        ({"CALC_AUTO_SAVE": "maybe"}, "must be a boolean"),
        ({"CALC_PRECISION": "abc"}, "must be an integer"),
        ({"CALC_PRECISION": "1.5"}, "must be an integer"),
        ({"CALC_PRECISION": "16"}, "between 0 and 15"),
        ({"CALC_PRECISION": "-1"}, "between 0 and 15"),
        ({"CALC_LOG_LEVEL": "VERBOSE"}, "CALC_LOG_LEVEL must be one of"),
    ],
)
def test_invalid_values_raise_configuration_error(env, message):
    with pytest.raises(ConfigurationError, match=message):
        CalculatorConfig.from_env(env)


def test_direct_construction_validates_precision():
    with pytest.raises(ConfigurationError, match="CALC_PRECISION"):
        CalculatorConfig(precision=99)


def test_direct_construction_validates_log_level():
    with pytest.raises(ConfigurationError, match="CALC_LOG_LEVEL"):
        CalculatorConfig(log_level="LOUD")


def test_from_env_without_mapping_loads_dotenv_then_reads_os_environ(monkeypatch):
    calls = []
    monkeypatch.setattr(config_module, "load_dotenv", lambda: calls.append(True))
    monkeypatch.setenv("CALC_PRECISION", "4")
    monkeypatch.delenv("CALC_AUTO_SAVE", raising=False)

    config = CalculatorConfig.from_env()

    assert calls == [True]
    assert config.precision == 4
    assert config.auto_save is True
