"""Validation of expressions typed into the REPL.

``parse_number`` demonstrates EAFP (attempt the conversion, handle the failure).
``split_expression`` demonstrates LBYL (check the shape before using it).
"""

import math

from app.exceptions import ValidationError

EXPRESSION_HELP = "expected format: <number> <operator> <number>, e.g. '3 + 4'"


def split_expression(line: str) -> tuple[str, str, str]:
    """Split ``line`` into ``(left, operator, right)``.

    LBYL: the token count is checked before unpacking.
    """
    tokens = line.split()
    if len(tokens) != 3:
        raise ValidationError(EXPRESSION_HELP)
    left, operator, right = tokens
    return left, operator, right


def parse_number(text: str) -> float:
    """Convert ``text`` to a finite float.

    EAFP: the conversion is attempted and a ``ValueError`` is translated into
    a ``ValidationError``.
    """
    try:
        value = float(text)
    except ValueError as exc:
        raise ValidationError(f"not a number: {text!r}") from exc
    if not math.isfinite(value):  # LBYL: NaN and infinity parse fine but are rejected
        raise ValidationError(f"number must be finite: {text!r}")
    return value
