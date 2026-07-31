"""Build interpolating functions that morph between SVG paths."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Literal

from .normalize import Origin, normalize_paths
from .path import Path
from .render import make_formatter, render_path

EPSILON = 2.0**-52


def mix_points(a: Sequence[float], b: Sequence[float], offset: float) -> list[float]:
    """Elementwise linear interpolation between two equal-length buffers."""
    return [a[i] + (b[i] - a[i]) * offset for i in range(len(a))]


def _get_path_interpolator(
    left: Path,
    right: Path,
    *,
    optimize: str,
    origin: Origin,
    add_points: int,
) -> Callable[[float], list[list[float]] | str]:
    matrix = normalize_paths(
        left.get_data(), right.get_data(), optimize=optimize, origin=origin, add_points=add_points
    )

    def interpolator(offset: float) -> list[list[float]] | str:
        if abs(offset) < EPSILON:
            return left.get_string_data()
        if abs(offset - 1) < EPSILON:
            return right.get_string_data()
        return [mix_points(matrix[0][h], matrix[1][h], offset) for h in range(len(matrix[0]))]

    return interpolator


def interpolate(
    paths: Sequence[str | Path | Sequence[Sequence[float]]],
    *,
    add_points: int = 0,
    optimize: Literal["fill", "none"] = "fill",
    origin: tuple[float, float] | Origin = (0.0, 0.0),
    precision: int = 0,
) -> Callable[[float], str]:
    """Return a function mapping offset in [0, 1] to an SVG path string.

    paths: two or more paths (d-strings, Path objects, or poly-bezier data).
        With more than two, the offset range is divided evenly between
        consecutive pairs.
    add_points: extra curves added to every subpath (use to smooth morphs
        between paths of very different complexity).
    optimize: "fill" (default) aligns subpaths automatically; "none" requires
        both paths to already have matching structure.
    origin: where filled subpaths grow from and where closed subpaths start
        drawing; relative to each subpath's bounding box unless wrapped in
        Origin(..., absolute=True).
    precision: decimal places in the output (0 = whole numbers, recommended).
    """
    if len(paths) < 2:
        raise ValueError("at least two paths are required")
    if optimize not in ("fill", "none"):
        raise ValueError(f"optimize must be 'fill' or 'none', got {optimize!r}")
    if add_points < 0:
        raise ValueError("add_points must be >= 0")
    if precision < 0:
        raise ValueError("precision must be >= 0")
    if not isinstance(origin, Origin):
        origin = Origin(*origin)

    path_objects = [path if isinstance(path, Path) else Path(path) for path in paths]
    hlen = len(path_objects) - 1
    items = [
        _get_path_interpolator(
            path_objects[h],
            path_objects[h + 1],
            optimize=optimize,
            origin=origin,
            add_points=add_points,
        )
        for h in range(hlen)
    ]
    formatter = make_formatter(precision)

    def morph(offset: float) -> str:
        d = hlen * offset
        flr = min(max(math.floor(d), 0), hlen - 1)
        return render_path(items[flr](d - flr), formatter)

    return morph
