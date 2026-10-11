"""Read-Eval-Print Loop: the interactive front end for the calculator."""

import sys
from collections.abc import Callable
from typing import TextIO

from app.calculator import Calculator
from app.exceptions import CalculatorError, ValidationError

PROMPT = "calc> "

HELP_TEXT = """\
Enter a calculation as: <number> <operator> <number>    e.g.  3 + 4   or   27 root 3
Operators: +  -  *  /  ^ (power)  root (b-th root of a: a root b)

Commands:
  help             show this message
  history [n]      show all calculations, or only the last n
  clear            clear the history (can be undone)
  undo / redo      step backwards / forwards through history changes
  save [path]      save history to CSV (default: CALC_HISTORY_FILE)
  load [path]      load history from CSV (can be undone)
  exit / quit      leave the calculator"""


def _parse_limit(args: list[str]) -> int | None:
    """Return the optional row limit given to ``history``."""
    if not args:
        return None
    try:  # EAFP: attempt the conversion and report a friendly error if it fails
        limit = int(args[0])
    except ValueError as exc:
        raise ValidationError(f"history limit must be a whole number: {args[0]!r}") from exc
    if limit < 1:
        raise ValidationError("history limit must be at least 1")
    return limit


class CalculatorREPL:
    """Reads lines, dispatches commands or calculations, and prints results."""

    def __init__(
        self,
        calculator: Calculator,
        input_fn: Callable[[str], str] = input,
        output: TextIO = sys.stdout,
    ) -> None:
        self._calculator = calculator
        self._input = input_fn
        self._out = output
        self._running = False
        self._commands: dict[str, Callable[[list[str]], None]] = {
            "help": self._cmd_help,
            "history": self._cmd_history,
            "clear": self._cmd_clear,
            "undo": self._cmd_undo,
            "redo": self._cmd_redo,
            "save": self._cmd_save,
            "load": self._cmd_load,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

    def run(self) -> None:
        """Loop until the user exits or the input stream ends."""
        self._running = True
        self._write("Calculator ready. Type 'help' for commands, 'exit' to quit.")
        while self._running:
            try:
                line = self._input(PROMPT)
            except (EOFError, KeyboardInterrupt):
                self._write("")
                break
            self.handle(line)

    def handle(self, line: str) -> None:
        """Process one line of input. Errors are printed, never raised."""
        tokens = line.split()
        if not tokens:
            return
        handler = self._commands.get(tokens[0].lower())
        try:
            if handler is None:
                self._cmd_calculate(line)
            else:
                handler(tokens[1:])
        except CalculatorError as exc:
            self._write(f"Error: {exc}")

    def _write(self, text: str) -> None:
        print(text, file=self._out)

    def _cmd_calculate(self, line: str) -> None:
        calculation = self._calculator.calculate_expression(line)
        self._write(calculation.describe(self._calculator.config.precision))

    def _cmd_help(self, _args: list[str]) -> None:
        self._write(HELP_TEXT)

    def _cmd_history(self, args: list[str]) -> None:
        frame = self._calculator.history_frame(_parse_limit(args))
        if frame.empty:
            self._write("No calculations yet.")
            return
        self._write(frame.to_string(index=False))

    def _cmd_clear(self, _args: list[str]) -> None:
        self._calculator.clear()
        self._write("History cleared.")

    def _cmd_undo(self, _args: list[str]) -> None:
        self._calculator.undo()
        self._write("Undone.")

    def _cmd_redo(self, _args: list[str]) -> None:
        self._calculator.redo()
        self._write("Redone.")

    def _cmd_save(self, args: list[str]) -> None:
        path = self._calculator.save(" ".join(args) or None)
        self._write(f"History saved to {path}.")

    def _cmd_load(self, args: list[str]) -> None:
        path = self._calculator.load(" ".join(args) or None)
        self._write(f"History loaded from {path}.")

    def _cmd_exit(self, _args: list[str]) -> None:
        self._running = False
        self._write("Goodbye!")
