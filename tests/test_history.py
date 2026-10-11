"""Tests for the pandas-backed history and its CSV persistence."""

from datetime import datetime

import pandas as pd
import pytest

from app.calculation import Calculation
from app.exceptions import HistoryError
from app.history import COLUMNS, History


def make_calc(a=2.0, op="+", b=3.0, result=5.0):
    return Calculation(a, op, b, result, datetime(2024, 1, 2, 3, 4, 5))


@pytest.fixture
def history():
    h = History()
    h.add(make_calc())
    h.add(make_calc(4, "*", 5, 20))
    h.add(make_calc(9, "-", 1, 8))
    return h


def test_new_history_is_empty_with_expected_columns():
    h = History()
    assert len(h) == 0
    assert list(h.frame().columns) == list(COLUMNS)


def test_add_appends_row_with_expected_values(history):
    frame = history.frame()
    assert len(history) == 3
    assert frame.iloc[0].to_dict() == {
        "timestamp": "2024-01-02T03:04:05",
        "operand_a": 2.0,
        "operator": "+",
        "operand_b": 3.0,
        "result": 5.0,
    }


def test_frame_returns_a_copy(history):
    frame = history.frame()
    frame.loc[0, "result"] = 999
    assert history.frame().loc[0, "result"] == 5.0


def test_tail_returns_last_rows(history):
    tail = history.tail(2)
    assert list(tail["operator"]) == ["*", "-"]


def test_tail_returns_copy(history):
    tail = history.tail(1)
    tail.loc[2, "operator"] = "changed"
    assert history.frame().loc[2, "operator"] == "-"


@pytest.mark.parametrize(
    "symbol, expected_count",
    [("+", 1), ("*", 1), ("/", 0), ("root", 0)],
)
def test_by_operator_filters_rows(history, symbol, expected_count):
    assert len(history.by_operator(symbol)) == expected_count


def test_by_operator_returns_copy(history):
    selected = history.by_operator("+")
    selected.loc[0, "result"] = 0
    assert history.frame().loc[0, "result"] == 5.0


def test_clear_removes_all_rows(history):
    history.clear()
    assert len(history) == 0


def test_restore_replaces_contents_with_copy(history):
    replacement = pd.DataFrame([make_calc(1, "+", 1, 2).to_record()], columns=COLUMNS)
    history.restore(replacement)
    replacement.loc[0, "result"] = 0
    assert len(history) == 1
    assert history.frame().loc[0, "result"] == 2.0


def test_save_csv_round_trips_through_read_csv(history, tmp_path):
    path = history.save_csv(tmp_path / "history.csv")
    loaded = History.read_csv(path)
    # check_dtype=False: pandas 3 reads text columns as its string dtype, not object.
    pd.testing.assert_frame_equal(loaded, history.frame(), check_dtype=False)


def test_write_csv_creates_missing_parent_folders(history, tmp_path):
    target = tmp_path / "nested" / "deeper" / "history.csv"
    assert History.write_csv(history.frame(), target) == target
    assert target.exists()


def test_write_csv_without_index_column(history, tmp_path):
    path = history.save_csv(tmp_path / "history.csv")
    assert list(pd.read_csv(path).columns) == list(COLUMNS)


def test_write_csv_to_directory_path_raises(history, tmp_path):
    with pytest.raises(HistoryError, match="could not save history"):
        History.write_csv(history.frame(), tmp_path)


def test_write_csv_when_parent_is_a_file_raises(history, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    with pytest.raises(HistoryError, match="could not save history"):
        History.write_csv(history.frame(), blocker / "history.csv")


def test_read_csv_missing_file_raises(tmp_path):
    with pytest.raises(HistoryError, match="not found"):
        History.read_csv(tmp_path / "missing.csv")


def test_read_csv_directory_raises(tmp_path):
    with pytest.raises(HistoryError, match="could not read history"):
        History.read_csv(tmp_path)


def test_read_csv_empty_file_raises(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(HistoryError, match="could not read history"):
        History.read_csv(path)


def test_read_csv_unparseable_file_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_bytes(b"\x00\xff\xfe\x00")
    with pytest.raises(HistoryError, match="could not read history|unexpected columns"):
        History.read_csv(path)


@pytest.mark.parametrize("content", ["x,y\n1,2\n", "timestamp,operand_a\n2024,1\n"])
def test_read_csv_wrong_columns_raises(tmp_path, content):
    path = tmp_path / "wrong.csv"
    path.write_text(content)
    with pytest.raises(HistoryError, match="unexpected columns"):
        History.read_csv(path)
