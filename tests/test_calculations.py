"""Tests for Calculation, the Calculator facade, and observers."""

import logging
from datetime import datetime

import pandas as pd
import pytest

from app.calculation import Calculation
from app.calculator import (
    AutoSaveObserver,
    Calculator,
    CalculatorEvent,
    CalculatorObserver,
    LoggingObserver,
)
from app.calculator_config import CalculatorConfig
from app.exceptions import DivisionByZeroError, HistoryError, MementoError, ValidationError
from app.history import History

WHEN = datetime(2024, 5, 6, 7, 8, 9)


class RecordingObserver(CalculatorObserver):
    """Test double that remembers every event it receives."""

    def __init__(self):
        self.events: list[CalculatorEvent] = []

    def update(self, event):
        self.events.append(event)


# --- Calculation -----------------------------------------------------------


@pytest.mark.parametrize(
    "a, op, b, expected",
    [
        (2, "+", 3, 5),
        (2, "-", 3, -1),
        (2, "*", 3, 6),
        (6, "/", 3, 2),
        (2, "^", 3, 8),
        (27, "root", 3, 3),
        (2, "pow", 3, 8),
    ],
)
def test_perform_runs_the_operation(a, op, b, expected):
    calculation = Calculation.perform(a, op, b)
    assert calculation.result == pytest.approx(expected)
    assert calculation.operand_a == a
    assert calculation.operand_b == b


def test_perform_normalises_operator_to_symbol():
    assert Calculation.perform(1, "add", 1).operator == "+"


def test_perform_propagates_operation_errors():
    with pytest.raises(DivisionByZeroError):
        Calculation.perform(1, "/", 0)


def test_to_record_matches_history_columns():
    calculation = Calculation(2, "+", 3, 5, WHEN)
    assert calculation.to_record() == {
        "timestamp": "2024-05-06T07:08:09",
        "operand_a": 2,
        "operator": "+",
        "operand_b": 3,
        "result": 5,
    }


def test_timestamp_defaults_to_now():
    assert isinstance(Calculation(1, "+", 1, 2).timestamp, datetime)


@pytest.mark.parametrize(
    "calculation, precision, expected",
    [
        (Calculation(3, "+", 4, 7, WHEN), 6, "3 + 4 = 7"),
        (Calculation(1, "/", 3, 1 / 3, WHEN), 6, "1 / 3 = 0.333333"),
        (Calculation(1, "/", 3, 1 / 3, WHEN), 2, "1 / 3 = 0.33"),
        (Calculation(2.5, "*", 2, 5.0, WHEN), 6, "2.5 * 2 = 5"),
    ],
)
def test_describe_formats_result_to_precision(calculation, precision, expected):
    assert calculation.describe(precision) == expected


# --- Calculator: expressions and arithmetic --------------------------------


@pytest.mark.parametrize(
    "line, expected",
    [("2 + 3", 5), ("10 - 4", 6), ("3 * -2", -6), ("8 / 2", 4), ("2 ^ 4", 16), ("8 root 3", 2)],
)
def test_calculate_expression_parses_and_computes(calculator, line, expected):
    assert calculator.calculate_expression(line).result == pytest.approx(expected)


@pytest.mark.parametrize(
    "line, error",
    [
        ("2 +", ValidationError),
        ("two + 3", ValidationError),
        ("2 % 3", ValidationError),
        ("1 / 0", DivisionByZeroError),
        ("inf + 1", ValidationError),
    ],
)
def test_calculate_expression_reports_bad_input(calculator, line, error):
    with pytest.raises(error):
        calculator.calculate_expression(line)


def test_failed_calculation_does_not_change_history(calculator):
    calculator.calculate(1, "+", 1)
    with pytest.raises(DivisionByZeroError):
        calculator.calculate(1, "/", 0)
    assert len(calculator.history_frame()) == 1
    assert calculator.can_undo is True


def test_calculate_records_row_and_returns_calculation(calculator):
    result = calculator.calculate(4, "*", 5)
    assert result.result == 20
    assert len(calculator.history_frame()) == 1


def test_history_frame_limit_returns_tail(calculator):
    for n in range(5):
        calculator.calculate(n, "+", 1)
    assert list(calculator.history_frame(2)["operand_a"]) == [3, 4]
    assert len(calculator.history_frame()) == 5


# --- Calculator: undo / redo / clear ---------------------------------------


def test_undo_and_redo_restore_history(calculator):
    calculator.calculate(1, "+", 1)
    calculator.calculate(2, "+", 2)

    calculator.undo()
    assert len(calculator.history_frame()) == 1
    assert calculator.can_redo

    calculator.redo()
    assert len(calculator.history_frame()) == 2
    assert not calculator.can_redo


def test_undo_with_nothing_to_undo_raises(calculator):
    with pytest.raises(MementoError):
        calculator.undo()


def test_redo_with_nothing_to_redo_raises(calculator):
    with pytest.raises(MementoError):
        calculator.redo()


def test_new_calculation_after_undo_discards_redo(calculator):
    calculator.calculate(1, "+", 1)
    calculator.undo()
    calculator.calculate(5, "+", 5)
    assert not calculator.can_redo


def test_clear_empties_history_and_can_be_undone(calculator):
    calculator.calculate(1, "+", 1)
    calculator.clear()
    assert len(calculator.history_frame()) == 0

    calculator.undo()
    assert len(calculator.history_frame()) == 1


def test_undo_and_redo_properties_track_stacks(calculator):
    assert not calculator.can_undo
    calculator.calculate(1, "+", 1)
    assert calculator.can_undo


# --- Calculator: persistence -----------------------------------------------


def test_save_writes_default_history_file(calculator, config):
    calculator.calculate(1, "+", 2)
    assert calculator.save() == config.history_file
    assert len(History.read_csv(config.history_file)) == 1


def test_save_to_custom_path(calculator, tmp_path):
    calculator.calculate(1, "+", 2)
    target = calculator.save(tmp_path / "custom.csv")
    assert target == tmp_path / "custom.csv"
    assert target.exists()


def test_load_restores_history_and_is_undoable(calculator, tmp_path):
    calculator.calculate(1, "+", 2)
    saved = calculator.save(tmp_path / "saved.csv")
    calculator.clear()

    assert calculator.load(saved) == saved
    assert len(calculator.history_frame()) == 1

    calculator.undo()
    assert len(calculator.history_frame()) == 0


def test_load_default_path(calculator, config):
    calculator.calculate(3, "+", 3)
    calculator.save()
    calculator.clear()
    calculator.load()
    assert len(calculator.history_frame()) == 1


def test_load_missing_file_leaves_state_unchanged(calculator, tmp_path):
    calculator.calculate(1, "+", 1)
    with pytest.raises(HistoryError):
        calculator.load(tmp_path / "missing.csv")
    assert len(calculator.history_frame()) == 1
    assert calculator.can_undo


def test_constructor_restores_existing_history_file(config):
    first = Calculator(config)
    first.calculate(7, "+", 1)
    first.save()

    second = Calculator(config)
    assert len(second.history_frame()) == 1
    assert second.history_frame().loc[0, "result"] == 8


def test_constructor_starts_empty_without_history_file(config):
    assert not config.history_file.exists()
    assert len(Calculator(config).history_frame()) == 0


def test_constructor_defaults_to_standard_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    calculator = Calculator()
    assert calculator.config == CalculatorConfig()


# --- Observers --------------------------------------------------------------


def test_observers_receive_every_change_event(config, tmp_path):
    seed = Calculator(config)
    seed.calculate(9, "+", 9)
    saved = seed.save(tmp_path / "seed.csv")

    observer = RecordingObserver()
    calculator = Calculator(config, observers=[observer])
    calculator.calculate(1, "+", 1)
    calculator.undo()
    calculator.redo()
    calculator.clear()
    calculator.load(saved)

    names = [event.name for event in observer.events]
    assert names == ["calculated", "undo", "redo", "cleared", "loaded"]


def test_observer_events_carry_calculation_and_history(config):
    observer = RecordingObserver()
    calculator = Calculator(config)
    calculator.subscribe(observer)
    calculation = calculator.calculate(2, "*", 4)

    event = observer.events[0]
    assert event.calculation == calculation
    assert len(event.history) == 1
    assert event.history.loc[0, "result"] == 8


def test_non_calculation_events_have_no_calculation(config):
    observer = RecordingObserver()
    calculator = Calculator(config, observers=[observer])
    calculator.clear()
    assert observer.events[0].calculation is None


def test_save_does_not_notify_observers(config):
    observer = RecordingObserver()
    calculator = Calculator(config, observers=[observer])
    calculator.save()
    assert observer.events == []


def test_logging_observer_logs_event(caplog):
    observer = LoggingObserver()
    event = CalculatorEvent("calculated", pd.DataFrame({"result": [1, 2]}))
    with caplog.at_level(logging.INFO, logger="app.calculator"):
        observer.update(event)
    assert "event=calculated history_size=2" in caplog.text


def test_autosave_observer_writes_history_after_each_change(config):
    calculator = Calculator(config, observers=[AutoSaveObserver(config.history_file)])
    calculator.calculate(1, "+", 2)
    calculator.calculate(3, "+", 4)
    assert len(History.read_csv(config.history_file)) == 2


def test_autosave_failure_is_logged_not_raised(tmp_path, caplog):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    calculator = Calculator(observers=[AutoSaveObserver(blocker / "history.csv")])
    with caplog.at_level(logging.WARNING, logger="app.calculator"):
        calculator.calculate(1, "+", 1)
    assert "auto-save failed" in caplog.text
    assert len(calculator.history_frame()) == 1

