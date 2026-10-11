"""Memento pattern: snapshots of history state that support undo and redo.

``CalculatorMemento`` is an immutable snapshot. ``CalculatorCaretaker`` owns the
undo and redo stacks and stores snapshots without inspecting them.
"""

from dataclasses import dataclass

import pandas as pd

from app.exceptions import MementoError


@dataclass(frozen=True, eq=False)  # eq=False: comparing DataFrames would be ambiguous
class CalculatorMemento:
    """A snapshot of the history at one point in time."""

    state: pd.DataFrame

    @classmethod
    def capture(cls, frame: pd.DataFrame) -> "CalculatorMemento":
        """Create a snapshot holding its own copy of ``frame``."""
        return cls(frame.copy())


class CalculatorCaretaker:
    """Keeps the undo and redo stacks of mementos."""

    def __init__(self) -> None:
        self._undo_stack: list[CalculatorMemento] = []
        self._redo_stack: list[CalculatorMemento] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def save(self, memento: CalculatorMemento) -> None:
        """Record a state before it changes. A new change invalidates the redo stack."""
        self._undo_stack.append(memento)
        self._redo_stack.clear()

    def undo(self, current: CalculatorMemento) -> CalculatorMemento:
        """Return the previous state and keep ``current`` so it can be redone."""
        if not self.can_undo:  # LBYL: check before popping
            raise MementoError("nothing to undo")
        self._redo_stack.append(current)
        return self._undo_stack.pop()

    def redo(self, current: CalculatorMemento) -> CalculatorMemento:
        """Return the next state and keep ``current`` so it can be undone."""
        if not self.can_redo:
            raise MementoError("nothing to redo")
        self._undo_stack.append(current)
        return self._redo_stack.pop()
