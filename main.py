"""Command-line entry point.

Run with:  python main.py
"""

import logging
import sys

from app.calculator import AutoSaveObserver, Calculator, LoggingObserver
from app.calculator_config import CalculatorConfig
from app.calculator_repl import CalculatorREPL
from app.exceptions import CalculatorError

EXIT_STARTUP_ERROR = 1


def main() -> int:
    """Load configuration, wire up the calculator and its observers, and start the REPL."""
    try:
        config = CalculatorConfig.from_env()
    except CalculatorError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return EXIT_STARTUP_ERROR

    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    observers = [LoggingObserver()]
    if config.auto_save:
        observers.append(AutoSaveObserver(config.history_file))

    try:
        calculator = Calculator(config, observers)
    except CalculatorError as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return EXIT_STARTUP_ERROR

    CalculatorREPL(calculator, output=sys.stdout).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
