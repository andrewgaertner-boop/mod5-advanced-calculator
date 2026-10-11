# Enhanced Calculator

An interactive command-line calculator with a REPL, undo/redo, CSV-backed history
(managed with pandas), environment-based configuration, and a full pytest suite
with 100% line and branch coverage enforced by GitHub Actions.

## Features

- **REPL** – type calculations such as `3 + 4` or `27 root 3` and see results immediately.
- **Operations** – addition, subtraction, multiplication, division, power, and nth root.
- **Undo / redo** – every change to the history can be reversed and re-applied.
- **History** – stored in a pandas DataFrame, shown with `history [n]`.
- **Persistence** – history is restored at startup, saved automatically after each change
  (optional), and can be saved or loaded manually.
- **Configuration** – read from environment variables or a `.env` file, validated at startup.
- **Error handling** – invalid input, division by zero, overflow, and bad files are reported
  without crashing the session.

## Setup

Requires Python 3.11 or newer.

```powershell
# Windows PowerShell
cd D:\AI\repos\calculator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux / Git Bash
python -m venv .venv
source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate
pip install -r requirements.txt
```

Optionally copy the example configuration and edit it:

```bash
cp .env.example .env
```

## Usage

```bash
python main.py
```

```text
Calculator ready. Type 'help' for commands, 'exit' to quit.
calc> 2 + 3
2 + 3 = 5
calc> 27 root 3
27 root 3 = 3
calc> 10 / 0
Error: division by zero
calc> history
          timestamp operand_a operator operand_b result
2026-10-11T10:29:03       2.0        +       3.0    5.0
2026-10-11T10:29:03      27.0     root       3.0    3.0
calc> undo
Undone.
calc> exit
Goodbye!
```

### Operators

| Symbol | Name(s) accepted        | Meaning                                  |
|--------|-------------------------|------------------------------------------|
| `+`    | `add`                   | `a + b`                                  |
| `-`    | `sub`, `subtract`       | `a - b`                                  |
| `*`    | `mul`, `multiply`       | `a * b`                                  |
| `/`    | `div`, `divide`         | `a / b` (zero divisor is an error)       |
| `^`    | `**`, `pow`, `power`    | `a` raised to the power `b`              |
| `root` | –                       | `b`-th root of `a` (`-8 root 3` is `-2`) |

Operator names are case-insensitive.

### Commands

| Command        | Action                                                        |
|----------------|---------------------------------------------------------------|
| `help`         | Show help text                                                |
| `history [n]`  | Show all calculations, or only the last `n`                   |
| `clear`        | Empty the history (can be undone)                             |
| `undo`         | Revert the last history change                                |
| `redo`         | Re-apply the last undone change                               |
| `save [path]`  | Save history to CSV (default: `CALC_HISTORY_FILE`)            |
| `load [path]`  | Replace history with a CSV file (can be undone)               |
| `exit` / `quit`| Leave the calculator                                          |

Paths may contain spaces: `save my results.csv`.

A new calculation after an undo discards the redo stack, as in most editors.

## Configuration

Settings come from environment variables. A `.env` file in the working directory is
loaded automatically; real environment variables take precedence over it.

| Variable            | Default           | Description                                              |
|---------------------|-------------------|----------------------------------------------------------|
| `CALC_HISTORY_FILE` | `data/history.csv`| CSV file for history persistence (relative to the cwd)   |
| `CALC_AUTO_SAVE`    | `true`            | Save history after every change (`true`/`false`)         |
| `CALC_PRECISION`    | `6`               | Significant digits in results (`0`–`15`)                 |
| `CALC_LOG_LEVEL`    | `WARNING`         | `DEBUG`, `INFO`, `WARNING`, or `ERROR`                   |

Invalid values stop the program at startup with a `Configuration error:` message.
Blank values use the default. Set `CALC_LOG_LEVEL=INFO` to see one log line per event.

## Project layout

```text
calculator/
├── main.py                       # entry point: python main.py
├── app/
│   ├── calculator_repl.py        # REPL: reads lines, dispatches commands
│   ├── calculator.py             # Calculator facade + observers
│   ├── calculation.py            # Calculation value object
│   ├── operations.py             # Strategy operations + OperationFactory
│   ├── history.py                # pandas-backed history and CSV I/O
│   ├── calculator_memento.py     # memento snapshots + undo/redo caretaker
│   ├── calculator_config.py      # env/.env configuration and validation
│   ├── input_validators.py       # input parsing (LBYL and EAFP examples)
│   └── exceptions.py             # CalculatorError hierarchy
├── tests/                        # pytest suites, parameterized where useful
├── .github/workflows/python-app.yml
├── requirements.txt
├── pytest.ini
├── .coveragerc
└── .env.example
```

## Design patterns

| Pattern    | Where                                   | Role                                                                 |
|------------|-----------------------------------------|----------------------------------------------------------------------|
| Strategy   | `operations.py`                         | Each `Operation` subclass is an interchangeable algorithm.           |
| Factory    | `operations.py` → `OperationFactory`    | Creates the right strategy from a symbol or name.                    |
| Observer   | `calculator.py` → `CalculatorObserver`  | `LoggingObserver` and `AutoSaveObserver` react to history events.    |
| Memento    | `calculator_memento.py`                 | Snapshots of history; the caretaker manages undo/redo stacks.        |
| Facade     | `calculator.py` → `Calculator`          | One simple API hides history, undo, persistence, and observers.      |

## Error handling

All deliberate failures derive from `CalculatorError` (see `exceptions.py`), so the REPL
catches a single base class and prints a message.

- **LBYL (Look Before You Leap)** – checks made before acting: the token count in
  `split_expression`, the divisor in `Divide`, the operator in `OperationFactory.create`,
  the undo/redo stacks, the CSV column names, and the configuration ranges.
- **EAFP (Easier to Ask Forgiveness than Permission)** – attempt the action and handle the
  failure: `parse_number` (`float()`), `_real_pow` (overflow, zero-division, complex results),
  `History.read_csv` / `write_csv` (I/O and parse errors), and the integer parsing in config
  and `history [n]`.

## Testing

```bash
pytest                                              # run all tests
pytest --cov=app --cov-report=term-missing tests/   # with coverage
coverage report --fail-under=100                    # enforce the coverage gate
```

The suite lives in `tests/`, one module per area, with parameterized tests for valid and
invalid inputs. `.coveragerc` enables branch coverage. The code has no `pass` or `continue`
statements that need `# pragma: no cover`, so none were added.

## Continuous integration

`.github/workflows/python-app.yml` runs on pushes and pull requests to `main`. It installs
`requirements.txt`, runs the tests with coverage, and fails the build if coverage is below
100%.
