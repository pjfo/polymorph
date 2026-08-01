"""Parse SVG path data into poly-bezier arrays.

Every path command (M/H/V/L/Z/C/S/Q/T/A, absolute or relative) is converted
to absolute cubic bezier curves. Each subpath becomes one flat list:
[move_x, move_y, then repeating 6-tuples (c1x, c1y, c2x, c2y, end_x, end_y)].
"""

from __future__ import annotations

import re

from .arc import arc_to_curve

# number of arguments each command consumes per repetition
ARG_LENGTHS = {"M": 2, "H": 1, "V": 1, "L": 2, "Z": 0, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}

QUADRATIC_RATIO = 2.0 / 3

# normalize every token (command letter or number) to be space-prefixed,
# discarding commas and stray whitespace between tokens
_TOKENS = re.compile(r"[\^\s]*([mhvlzcsqta]|-?\d*\.?\d+)[,$\s]*", re.IGNORECASE)
# give command letters a second leading space so segments split on "  "
_COMMANDS = re.compile(r"([mhvlzcsqta])", re.IGNORECASE)


class _ParseContext:
    __slots__ = ("command", "current", "cx", "cy", "last_command", "segments", "terms", "x", "y")

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.cx = 0.0  # last control point, for smooth curve continuation
        self.cy = 0.0
        self.last_command: str | None = None
        self.command = ""
        self.terms: list[float] = []
        self.segments: list[list[float]] = []
        self.current: list[float] | None = None


def _coalesce(value: float | None, fallback: float) -> float:
    # 0.0 is a valid coordinate, so only None falls back (JS used undefined).
    return fallback if value is None else value


def _add_curve(
    ctx: _ParseContext,
    x1: float | None,
    y1: float | None,
    x2: float | None,
    y2: float | None,
    dx: float | None,
    dy: float | None,
) -> None:
    if ctx.current is None:
        raise ValueError("path data must start with a move (M/m) command")
    x = ctx.x
    y = ctx.y
    ctx.x = _coalesce(dx, x)
    ctx.y = _coalesce(dy, y)
    ctx.current.extend(
        (_coalesce(x1, x), _coalesce(y1, y), _coalesce(x2, x), _coalesce(y2, y), ctx.x, ctx.y)
    )
    ctx.last_command = ctx.command


def _convert_to_absolute(ctx: _ParseContext) -> None:
    c = ctx.command
    t = ctx.terms
    if c == "V":
        t[0] += ctx.y
    elif c == "H":
        t[0] += ctx.x
    elif c == "A":
        t[5] += ctx.x
        t[6] += ctx.y
    else:
        for j in range(0, len(t), 2):
            t[j] += ctx.x
            t[j + 1] += ctx.y


def _parse_segments(d: str) -> list[tuple[str, list[float]]]:
    normalized = _TOKENS.sub(r" \1", d)
    normalized = _COMMANDS.sub(r" \1", normalized).strip()
    segments = []
    for chunk in normalized.split("  "):
        parts = chunk.split(" ")
        command = parts[0]
        try:
            args = [float(p) for p in parts[1:]]
        except ValueError:
            raise ValueError(f"invalid number in path data near {chunk!r}") from None
        segments.append((command, args))
    return segments


def parse_points(d: str) -> list[list[float]]:
    """Parse SVG path data into a list of flat poly-bezier subpath arrays."""
    ctx = _ParseContext()

    for command_letter, args in _parse_segments(d):
        command = command_letter.upper()
        if command not in ARG_LENGTHS:
            raise ValueError(f"{command_letter!r} is not a supported path command")
        is_relative = command != "Z" and command != command_letter
        ctx.command = command
        max_length = ARG_LENGTHS[command]

        if max_length > 0 and not args:
            raise ValueError(f"{command_letter!r} requires {max_length} argument(s)")

        # consume repeated argument sets (e.g. "L 1 2 3 4" is two lines)
        k = 0
        while True:
            ctx.terms = args[k : k + max_length]
            if len(ctx.terms) < max_length:
                raise ValueError(f"{command_letter!r} has insufficient arguments")

            if is_relative:
                _convert_to_absolute(ctx)

            n = ctx.terms
            x = ctx.x
            y = ctx.y

            if command == "M":
                ctx.x = n[0]
                ctx.y = n[1]
                ctx.current = [ctx.x, ctx.y]
                ctx.segments.append(ctx.current)
            elif command == "H":
                _add_curve(ctx, None, None, None, None, n[0], None)
            elif command == "V":
                _add_curve(ctx, None, None, None, None, None, n[0])
            elif command == "L":
                _add_curve(ctx, None, None, None, None, n[0], n[1])
            elif command == "Z":
                if ctx.current is None:
                    raise ValueError("path data must start with a move (M/m) command")
                _add_curve(ctx, None, None, None, None, ctx.current[0], ctx.current[1])
            elif command == "C":
                _add_curve(ctx, n[0], n[1], n[2], n[3], n[4], n[5])
                ctx.cx = n[2]
                ctx.cy = n[3]
            elif command == "S":
                is_initial = ctx.last_command not in ("S", "C")
                x1 = None if is_initial else x * 2 - ctx.cx
                y1 = None if is_initial else y * 2 - ctx.cy
                _add_curve(ctx, x1, y1, n[0], n[1], n[2], n[3])
                ctx.cx = n[0]
                ctx.cy = n[1]
            elif command == "Q":
                cx1, cy1, dx, dy = n
                _add_curve(
                    ctx,
                    x + (cx1 - x) * QUADRATIC_RATIO,
                    y + (cy1 - y) * QUADRATIC_RATIO,
                    dx + (cx1 - dx) * QUADRATIC_RATIO,
                    dy + (cy1 - dy) * QUADRATIC_RATIO,
                    dx,
                    dy,
                )
                ctx.cx = cx1
                ctx.cy = cy1
            elif command == "T":
                dx, dy = n
                if ctx.last_command in ("Q", "T"):
                    # reflect the previous quadratic control point
                    x1 = x + (x * 2 - ctx.cx - x) * QUADRATIC_RATIO
                    y1 = y + (y * 2 - ctx.cy - y) * QUADRATIC_RATIO
                    x2 = dx + (x * 2 - ctx.cx - dx) * QUADRATIC_RATIO
                    y2 = dy + (y * 2 - ctx.cy - dy) * QUADRATIC_RATIO
                else:
                    x1 = x2 = x
                    y1 = y2 = y
                _add_curve(ctx, x1, y1, x2, y2, dx, dy)
                ctx.cx = x2
                ctx.cy = y2
            elif command == "A":
                beziers = arc_to_curve(x, y, n[0], n[1], n[2], n[3], n[4], n[5], n[6])
                for j in range(0, len(beziers), 6):
                    _add_curve(
                        ctx,
                        beziers[j],
                        beziers[j + 1],
                        beziers[j + 2],
                        beziers[j + 3],
                        beziers[j + 4],
                        beziers[j + 5],
                    )

            k += max_length
            if max_length == 0 or k >= len(args):
                break

    return ctx.segments
