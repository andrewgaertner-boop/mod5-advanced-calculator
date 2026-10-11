"""Calculation history stored in a pandas DataFrame, with CSV persistence."""

from pathlib import Path

import pandas as pd

from app.calculation import Calculation
from app.exceptions import HistoryError

COLUMNS: tuple[str, ...] = ("timestamp", "operand_a", "operator", "operand_b", "result")


class History:
    """Stores calculations as DataFrame rows and reads/writes them as CSV.

    This class is the *originator* in the memento pattern: its state is copied
    out with ``frame()`` and put back with ``restore()``.
    """

    def __init__(self) -> None:
        self._frame = pd.DataFrame(columns=COLUMNS)

    def __len__(self) -> int:
        return len(self._frame)

    def add(self, calculation: Calculation) -> None:
        """Append one calculation as a new row."""
        row = pd.DataFrame([calculation.to_record()], columns=COLUMNS)
        self._frame = pd.concat([self._frame, row], ignore_index=True)

    def frame(self) -> pd.DataFrame:
        """Return a copy of the full history, so callers cannot mutate it directly."""
        return self._frame.copy()

    def tail(self, count: int) -> pd.DataFrame:
        """Return a copy of the last ``count`` rows."""
        return self._frame.tail(count).copy()

    def by_operator(self, symbol: str) -> pd.DataFrame:
        """Return a copy of the rows whose operator equals ``symbol``."""
        return self._frame.loc[self._frame["operator"] == symbol].copy()

    def clear(self) -> None:
        """Remove every row."""
        self._frame = pd.DataFrame(columns=COLUMNS)

    def restore(self, frame: pd.DataFrame) -> None:
        """Replace the history with a copy of ``frame``."""
        self._frame = frame.copy()

    def save_csv(self, path: str | Path) -> Path:
        """Write the history to ``path`` as CSV and return the path."""
        return self.write_csv(self._frame, path)

    @staticmethod
    def write_csv(frame: pd.DataFrame, path: str | Path) -> Path:
        """Write ``frame`` to ``path``, creating parent folders as needed.

        EAFP: the write is attempted and any ``OSError`` is reported as a
        ``HistoryError``.
        """
        target = Path(path)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(target, index=False)
        except OSError as exc:
            raise HistoryError(f"could not save history to {target}: {exc}") from exc
        return target

    @staticmethod
    def read_csv(path: str | Path) -> pd.DataFrame:
        """Read and validate a history CSV file from ``path``.

        EAFP: pandas is asked to read the file and each failure mode is mapped
        to a ``HistoryError``.
        """
        target = Path(path)
        try:
            frame = pd.read_csv(target)
        except FileNotFoundError as exc:
            raise HistoryError(f"history file not found: {target}") from exc
        except (
            OSError,
            UnicodeDecodeError,
            pd.errors.ParserError,
            pd.errors.EmptyDataError,
        ) as exc:
            raise HistoryError(f"could not read history from {target}: {exc}") from exc
        if list(frame.columns) != list(COLUMNS):  # LBYL: reject files with the wrong shape
            raise HistoryError(f"unexpected columns in {target}: {list(frame.columns)}")
        return frame
