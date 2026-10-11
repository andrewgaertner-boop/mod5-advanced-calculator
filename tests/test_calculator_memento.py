"""Tests for the memento snapshots and the undo/redo caretaker."""

import pandas as pd
import pytest

from app.calculator_memento import CalculatorCaretaker, CalculatorMemento
from app.exceptions import MementoError


def frame_with(value):
    return pd.DataFrame({"result": [value]})


def test_capture_stores_a_copy_of_the_frame():
    source = frame_with(1.0)
    memento = CalculatorMemento.capture(source)
    source.loc[0, "result"] = 99.0
    assert memento.state.loc[0, "result"] == 1.0


@pytest.mark.parametrize("value", [0.0, -3.5, 1e9])
def test_capture_preserves_values(value):
    assert CalculatorMemento.capture(frame_with(value)).state.loc[0, "result"] == value


def test_new_caretaker_has_nothing_to_undo_or_redo():
    caretaker = CalculatorCaretaker()
    assert not caretaker.can_undo
    assert not caretaker.can_redo


def test_undo_with_empty_stack_raises():
    caretaker = CalculatorCaretaker()
    with pytest.raises(MementoError, match="nothing to undo"):
        caretaker.undo(CalculatorMemento.capture(frame_with(0)))


def test_redo_with_empty_stack_raises():
    caretaker = CalculatorCaretaker()
    with pytest.raises(MementoError, match="nothing to redo"):
        caretaker.redo(CalculatorMemento.capture(frame_with(0)))


def test_undo_returns_saved_state_and_enables_redo():
    caretaker = CalculatorCaretaker()
    before = CalculatorMemento.capture(frame_with(1))
    caretaker.save(before)
    current = CalculatorMemento.capture(frame_with(2))

    restored = caretaker.undo(current)

    assert restored is before
    assert caretaker.can_redo
    assert not caretaker.can_undo


def test_redo_returns_undone_state():
    caretaker = CalculatorCaretaker()
    caretaker.save(CalculatorMemento.capture(frame_with(1)))
    current = CalculatorMemento.capture(frame_with(2))
    caretaker.undo(current)

    redone = caretaker.redo(CalculatorMemento.capture(frame_with(1)))

    assert redone is current
    assert caretaker.can_undo
    assert not caretaker.can_redo


def test_saving_a_new_state_clears_redo_stack():
    caretaker = CalculatorCaretaker()
    caretaker.save(CalculatorMemento.capture(frame_with(1)))
    caretaker.undo(CalculatorMemento.capture(frame_with(2)))
    assert caretaker.can_redo

    caretaker.save(CalculatorMemento.capture(frame_with(3)))

    assert not caretaker.can_redo
    assert caretaker.can_undo


@pytest.mark.parametrize("steps", [1, 2, 3])
def test_repeated_undo_then_redo_walks_the_history(steps):
    caretaker = CalculatorCaretaker()
    for value in range(steps):
        caretaker.save(CalculatorMemento.capture(frame_with(value)))

    state = frame_with(100)
    for _ in range(steps):
        state = caretaker.undo(CalculatorMemento.capture(state)).state
    assert state.loc[0, "result"] == 0

    for _ in range(steps):
        state = caretaker.redo(CalculatorMemento.capture(state)).state
    assert state.loc[0, "result"] == 100
