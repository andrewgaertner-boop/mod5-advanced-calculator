"""Facade and observers for the calculator.

``Calculator`` is the simplified interface used by the REPL and any other
caller. Behind it, it coordinates the history, the memento caretaker and the
observers, so callers never touch those parts directly.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorCaretaker, CalculatorMemento
from app.exceptions import HistoryError
from app.history import History
from app.input_validators import parse_number, split_expression

logger = logging.getLogger(__name__)


@dataclass(frozen=True, eq=False)
class CalculatorEvent:
    """Describes a change to the history, delivered to every observer.

    ``name`` is one of ``calculated``, ``undo``, ``redo``, ``cleared`` or ``loaded``.
    """

    name: str
    history: pd.DataFrame
    calculation: Calculation | None = None


class CalculatorObserver(ABC):
    """Observer interface (*Observer pattern*): react to calculator events."""

    @abstractmethod
    def update(self, event: CalculatorEvent) -> None:
        """Handle a calculator event."""


class LoggingObserver(CalculatorObserver):
    """Writes one log line for each event."""

    def update(self, event: CalculatorEvent) -> None:
        logger.info("event=%s history_size=%d", event.name, len(event.history))


class AutoSaveObserver(CalculatorObserver):
    """Writes the full history to CSV after every change.

    A failed save is logged as a warning and does not interrupt the session.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def update(self, event: CalculatorEvent) -> None:
        try:
            History.write_csv(event.history, self._path)
        except HistoryError as exc:
            logger.warning("auto-save failed: %s", exc)


class Calculator:
    """Facade over arithmetic, history, undo/redo, persistence and observers."""

    def __init__(
        self,
        config: CalculatorConfig | None = None,
        observers: Iterable[CalculatorObserver] = (),
    ) -> None:
        self.config = config or CalculatorConfig()
        self._history = History()
        self._caretaker = CalculatorCaretaker()
        self._observers: list[CalculatorObserver] = list(observers)
        if self.config.history_file.exists():  # LBYL: restore previous session if present
            self._history.restore(History.read_csv(self.config.history_file))

    @property
    def can_undo(self) -> bool:
        return self._caretaker.can_undo

    @property
    def can_redo(self) -> bool:
        return self._caretaker.can_redo

    def subscribe(self, observer: CalculatorObserver) -> None:
        """Register an observer to receive future events."""
        self._observers.append(observer)

    def history_frame(self, limit: int | None = None) -> pd.DataFrame:
        """Return the whole history, or only the last ``limit`` rows."""
        if limit is None:
            return self._history.frame()
        return self._history.tail(limit)

    def calculate_expression(self, line: str) -> Calculation:
        """Parse a line such as ``3 + 4`` and perform the calculation."""
        left, operator, right = split_expression(line)
        return self.calculate(parse_number(left), operator, parse_number(right))

    def calculate(self, operand_a: float, operator: str, operand_b: float) -> Calculation:
        """Perform a calculation, record it, and notify observers."""
        # Performed first, so a failing operation leaves the state untouched.
        calculation = Calculation.perform(operand_a, operator, operand_b)
        self._record_state()
        self._history.add(calculation)
        self._notify("calculated", calculation)
        return calculation

    def undo(self) -> None:
        """Revert the most recent history change."""
        previous = self._caretaker.undo(self._snapshot())
        self._history.restore(previous.state)
        self._notify("undo")

    def redo(self) -> None:
        """Re-apply the most recently undone history change."""
        following = self._caretaker.redo(self._snapshot())
        self._history.restore(following.state)
        self._notify("redo")

    def clear(self) -> None:
        """Empty the history. This change can be undone."""
        self._record_state()
        self._history.clear()
        self._notify("cleared")

    def save(self, path: str | Path | None = None) -> Path:
        """Save the history to ``path``, or to the configured history file by default."""
        return self._history.save_csv(path or self.config.history_file)

    def load(self, path: str | Path | None = None) -> Path:
        """Replace the history with the contents of ``path`` (undoable)."""
        target = Path(path or self.config.history_file)
        frame = History.read_csv(target)  # read first, so a bad file leaves state untouched
        self._record_state()
        self._history.restore(frame)
        self._notify("loaded")
        return target

    def _snapshot(self) -> CalculatorMemento:
        return CalculatorMemento.capture(self._history.frame())

    def _record_state(self) -> None:
        self._caretaker.save(self._snapshot())

    def _notify(self, name: str, calculation: Calculation | None = None) -> None:
        event = CalculatorEvent(name, self._history.frame(), calculation)
        for observer in self._observers:
            observer.update(event)
