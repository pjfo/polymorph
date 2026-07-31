"""Serialize poly-bezier data back to SVG path data."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

Formatter = Callable[[float], "str | float"]


def js_round(n: float) -> int:
    """Round half away from negative infinity, matching JavaScript's Math.round.

    Python's built-in round() is banker's rounding (round(2.5) == 2), which
    would produce different path strings than polymorph-js.
    """
    return math.floor(n + 0.5)


def _default_formatter(n: float) -> str:
    return str(js_round(n))


def make_formatter(precision: int) -> Formatter:
    """Return the number formatter for a given decimal precision.

    precision <= 0 rounds to whole numbers (recommended); precision > 0
    produces fixed-decimal output like JavaScript's toFixed.
    """
    if precision <= 0:
        return _default_formatter
    return lambda n: f"{n:.{precision}f}"


def render_path(ns: Sequence[Sequence[float]] | str, formatter: Formatter | None = None) -> str:
    """Convert poly-bezier data to an SVG path string.

    Each subpath is emitted as one M command followed by one C command with
    all curve coordinates. Strings pass through untouched (used by the
    offset 0/1 short-circuit in interpolate).
    """
    if isinstance(ns, str):
        return ns
    if formatter is None:
        formatter = _default_formatter

    result: list[str] = []
    for n in ns:
        result.extend(("M", str(formatter(n[0])), str(formatter(n[1])), "C"))
        last_result: str | None = None
        for f in range(2, len(n), 6):
            p0 = str(formatter(n[f]))
            p1 = str(formatter(n[f + 1]))
            p2 = str(formatter(n[f + 2]))
            p3 = str(formatter(n[f + 3]))
            dx = str(formatter(n[f + 4]))
            dy = str(formatter(n[f + 5]))

            is_point = p0 == dx and p2 == dx and p1 == dy and p3 == dy

            # Suppress consecutive duplicate degenerate point-curves. As in the
            # original, last_result is only updated when the curve is a point.
            if is_point:
                key = p0 + p1 + p2 + p3 + dx + dy
                if last_result == key:
                    continue
                last_result = key
            result.extend((p0, p1, p2, p3, dx, dy))
    return " ".join(result)
