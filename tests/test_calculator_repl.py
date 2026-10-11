"""Tests for the REPL: commands, calculations, and error reporting."""

import io

import pytest

from app.calculator import Calculator
from app.calculator_repl import CalculatorREPL, HELP_TEXT, PROMPT
from app.exceptions import ValidationError
from app.history import History


def run_session(calculator, lines):
    """Feed ``lines`` to a REPL and return everything it printed."""
    output = io.StringIO()
    queue = iter(lines)

    def fake_input(prompt):
        assert prompt == PROMPT
        try:
            return next(queue)
        except StopIteration:
            raise EOFError from None

    CalculatorREPL(calculator, input_fn=fake_input, output=output).run()
    return output.getvalue()


def repl_for(calculator):
    return CalculatorREPL(calculator, output=io.StringIO())


@pytest.mark.parametrize(
    "line, expected",
    [
        ("3 + 4", "3 + 4 = 7"),
        ("10 / 4", "10 / 4 = 2.5"),
        ("2 ^ 10", "2 ^ 10 = 1024"),
        ("27 root 3", "27 root 3 = 3"),
        ("1 / 3", "1 / 3 = 0.333333"),
    ],
)
def test_calculation_is_printed(calculator, line, expected):
    assert expected in run_session(calculator, [line, "exit"])


@pytest.mark.parametrize(
    "line, message",
    [
        ("1 / 0", "Error: division by zero"),
        ("2 % 3", "Error: unknown operation"),
        ("foo", "Error: expected format"),
        ("x + 1", "Error: not a number"),
        ("10 ^ 400", "Error: result is too large"),
    ],
)
def test_bad_input_reports_error_and_keeps_running(calculator, line, message):
    output = run_session(calculator, [line, "2 + 2"])
    assert message in output
    assert "2 + 2 = 4" in output


def test_blank_lines_are_ignored(calculator):
    output = run_session(calculator, ["", "   ", "exit"])
    assert "Error" not in output


@pytest.mark.parametrize("command", ["exit", "quit", "EXIT", "Quit"])
def test_exit_commands_stop_the_loop(calculator, command):
    output = run_session(calculator, [command, "1 + 1"])
    assert "Goodbye!" in output
    assert "= 2" not in output


def test_end_of_input_ends_loop(calculator):
    output = run_session(calculator, ["1 + 1"])
    assert "1 + 1 = 2" in output


def test_keyboard_interrupt_ends_loop(calculator):
    calls = []

    def interrupting_input(prompt):
        calls.append(prompt)
        raise KeyboardInterrupt

    output = io.StringIO()
    CalculatorREPL(calculator, input_fn=interrupting_input, output=output).run()
    assert calls == [PROMPT]


def test_help_prints_help_text(calculator):
    output = run_session(calculator, ["HELP", "exit"])
    assert HELP_TEXT in output


def test_history_when_empty(calculator):
    assert "No calculations yet." in run_session(calculator, ["history", "exit"])


def test_history_lists_all_calculations(calculator):
    calculator.calculate(2, "*", 3)
    lines = run_session(calculator, ["history", "exit"]).splitlines()
    assert lines[1].split() == ["timestamp", "operand_a", "operator", "operand_b", "result"]
    assert lines[2].split()[1:] == ["2", "*", "3", "6"]


@pytest.mark.parametrize("limit, row_count", [("1", 1), ("5", 2)])
def test_history_with_limit_shows_recent_rows(calculator, limit, row_count):
    calculator.calculate(1, "+", 1)
    calculator.calculate(2, "*", 3)
    lines = run_session(calculator, [f"history {limit}", "exit"]).splitlines()
    table = lines[1:-1]  # skip the ready message and the goodbye message
    assert len(table) == row_count + 1  # header row plus data rows


@pytest.mark.parametrize("limit", ["x", "1.5"])
def test_history_limit_must_be_whole_number(calculator, limit):
    output = run_session(calculator, [f"history {limit}", "exit"])
    assert "history limit must be a whole number" in output


@pytest.mark.parametrize("limit", ["0", "-3"])
def test_history_limit_must_be_positive(calculator, limit):
    output = run_session(calculator, [f"history {limit}", "exit"])
    assert "history limit must be at least 1" in output


def test_clear_empties_history_and_undo_restores_it(calculator):
    output = run_session(calculator, ["4 + 4", "clear", "history", "undo", "history", "exit"])
    assert "History cleared." in output
    assert "Undone." in output
    assert "No calculations yet." in output


def test_undo_and_redo_messages(calculator):
    output = run_session(calculator, ["1 + 1", "undo", "redo", "exit"])
    assert "Undone." in output
    assert "Redone." in output


def test_undo_with_nothing_reports_error(calculator):
    assert "Error: nothing to undo" in run_session(calculator, ["undo", "exit"])


def test_redo_with_nothing_reports_error(calculator):
    assert "Error: nothing to redo" in run_session(calculator, ["redo", "exit"])


def test_save_and_load_with_path_containing_spaces(calculator, tmp_path):
    target = tmp_path / "my history.csv"
    output = run_session(calculator, ["5 + 5", f"save {target}", "clear", f"load {target}", "exit"])
    assert f"History saved to {target}." in output
    assert f"History loaded from {target}." in output
    assert len(History.read_csv(target)) == 1


def test_save_and_load_default_paths(calculator, config):
    run_session(calculator, ["6 + 6", "save", "clear", "load", "exit"])
    assert config.history_file.exists()
    assert len(calculator.history_frame()) == 1


def test_load_missing_file_reports_error(calculator, tmp_path):
    output = run_session(calculator, [f"load {tmp_path / 'nope.csv'}", "exit"])
    assert "Error: history file not found" in output


def test_save_failure_reports_error(calculator, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    output = run_session(calculator, [f"save {blocker / 'h.csv'}", "exit"])
    assert "Error: could not save history" in output


def test_handle_ignores_empty_lines_and_returns_none(calculator):
    repl = repl_for(calculator)
    assert repl.handle("   ") is None
    assert len(calculator.history_frame()) == 0


def test_handle_processes_one_line_without_run(calculator):
    output = io.StringIO()
    CalculatorREPL(calculator, output=output).handle("7 - 2")
    assert "7 - 2 = 5" in output.getvalue()


def test_parse_limit_helper_rejects_non_numbers():
    from app.calculator_repl import _parse_limit

    with pytest.raises(ValidationError):
        _parse_limit(["many"])


def test_calculator_is_used_for_precision(config):
    from app.calculator_config import CalculatorConfig

    precise = Calculator(CalculatorConfig(history_file=config.history_file, precision=2))
    assert "1 / 3 = 0.33" in run_session(precise, ["1 / 3", "exit"])
