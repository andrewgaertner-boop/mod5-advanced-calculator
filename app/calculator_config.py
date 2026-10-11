"""Application configuration read from environment variables.

Values come from the process environment or from a ``.env`` file loaded with
python-dotenv. Blank or unset variables fall back to defaults. Every value is
validated, and invalid values raise ``ConfigurationError``.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigurationError

DEFAULT_HISTORY_FILE = "data/history.csv"
DEFAULT_PRECISION = 6
MIN_PRECISION = 0
MAX_PRECISION = 15
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True)
class CalculatorConfig:
    """Validated settings for one calculator session."""

    history_file: Path = Path(DEFAULT_HISTORY_FILE)
    auto_save: bool = True
    precision: int = DEFAULT_PRECISION
    log_level: str = "WARNING"

    def __post_init__(self) -> None:
        if not MIN_PRECISION <= self.precision <= MAX_PRECISION:  # LBYL range check
            raise ConfigurationError(
                f"CALC_PRECISION must be between {MIN_PRECISION} and {MAX_PRECISION}, "
                f"got {self.precision}"
            )
        if self.log_level not in LOG_LEVELS:
            raise ConfigurationError(
                f"CALC_LOG_LEVEL must be one of {', '.join(LOG_LEVELS)}, got {self.log_level!r}"
            )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "CalculatorConfig":
        """Build a config from ``env``, or from ``os.environ`` after loading ``.env``.

        Passing ``env`` explicitly skips the ``.env`` file, which keeps tests
        and callers isolated from the machine's settings.
        """
        if env is None:
            load_dotenv()  # fills os.environ from .env without overriding real variables
            env = os.environ
        defaults = cls()
        return cls(
            history_file=Path(_read(env, "CALC_HISTORY_FILE") or DEFAULT_HISTORY_FILE),
            auto_save=_parse_bool(env, "CALC_AUTO_SAVE", defaults.auto_save),
            precision=_parse_int(env, "CALC_PRECISION", defaults.precision),
            log_level=(_read(env, "CALC_LOG_LEVEL") or defaults.log_level).upper(),
        )


def _read(env: Mapping[str, str], name: str) -> str | None:
    """Return the stripped value of ``name``, or None when it is unset or blank."""
    return (env.get(name) or "").strip() or None


def _parse_bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = _read(env, name)
    if raw is None:
        return default
    lowered = raw.lower()
    if lowered in _TRUE_VALUES:
        return True
    if lowered in _FALSE_VALUES:
        return False
    raise ConfigurationError(f"{name} must be a boolean (true/false), got {raw!r}")


def _parse_int(env: Mapping[str, str], name: str, default: int) -> int:
    raw = _read(env, name)
    if raw is None:
        return default
    try:  # EAFP: attempt the conversion and report a friendly error if it fails
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from exc
