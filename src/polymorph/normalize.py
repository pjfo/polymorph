"""Normalize two parsed paths so they can be interpolated point-for-point."""

from __future__ import annotations

import math
from typing import NamedTuple


class Origin(NamedTuple):
    """Origin used to align subpaths before morphing.

    When absolute is False (default), x and y are fractions of each subpath's
    bounding box (0, 0 = top-left, 1, 1 = bottom-right). When True, they are
    absolute coordinates in the SVG coordinate space.
    """

    x: float
    y: float
    absolute: bool = False


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def perimeter_points(pts: list[float]) -> int:
    """Approximate a subpath's perimeter by summing distances between endpoints."""
    n = len(pts)
    x2 = pts[n - 2]
    y2 = pts[n - 1]
    p = 0.0
    for i in range(0, n, 6):
        p += distance(pts[i], pts[i + 1], x2, y2)
        x2 = pts[i]
        y2 = pts[i + 1]
    return math.floor(p)


def sorted_segments(segments: list[list[float]]) -> list[list[float]]:
    """Sort subpaths largest-perimeter first, so holes tend to pair with holes."""
    return sorted(segments, key=perimeter_points, reverse=True)


def compute_dimensions(points: list[float]) -> tuple[float, float, float, float]:
    """Bounding box (x, y, w, h) of a subpath's endpoints (control points ignored)."""
    xmin = xmax = points[0]
    ymin = ymax = points[1]
    for i in range(2, len(points), 6):
        x = points[i + 4]
        y = points[i + 5]
        xmin = min(xmin, x)
        xmax = max(xmax, x)
        ymin = min(ymin, y)
        ymax = max(ymax, y)
    return xmin, ymin, xmax - xmin, ymax - ymin


def compute_absolute_origin(
    relative_x: float, relative_y: float, points: list[float]
) -> tuple[float, float]:
    x, y, w, h = compute_dimensions(points)
    return x + w * relative_x, y + h * relative_y


def fill_segments(larger: list[list[float]], smaller: list[list[float]], origin: Origin) -> None:
    """Pad the shorter path with degenerate all-origin subpaths (in place).

    The extra subpaths collapse to a single point, so during a morph they
    appear to grow out of / shrink into the origin.
    """
    if len(larger) < len(smaller):
        fill_segments(smaller, larger, origin)
        return
    for i in range(len(smaller), len(larger)):
        source = larger[i]
        origin_x = origin.x
        origin_y = origin.y
        if not origin.absolute:
            origin_x, origin_y = compute_absolute_origin(origin_x, origin_y, source)
        degenerate = [0.0] * len(source)
        for k in range(0, len(source), 2):
            degenerate[k] = origin_x
            degenerate[k + 1] = origin_y
        smaller.append(degenerate)


def fill_subpath(ns: list[float], total_length: int) -> list[float]:
    """Grow a subpath to total_length by duplicating endpoints, spread evenly."""
    if total_length < len(ns) or (total_length - 2) % 6 != 0:
        raise ValueError("invalid target length for subpath fill")

    total_needed = total_length - len(ns)
    ratio = math.ceil(total_length / len(ns))
    result = [ns[0], ns[1]]
    dx = ns[0]
    dy = ns[1]

    for k in range(2, len(ns), 6):
        result.extend(ns[k : k + 6])
        dx = ns[k + 4]
        dy = ns[k + 5]

        # emit up to `ratio` degenerate point-curves at this endpoint
        f = 0
        while f < ratio and total_needed > 0:
            result.extend((dx, dy, dx, dy, dx, dy))
            total_needed -= 6
            f += 1

    # when total_length exceeds what the per-curve ratio can absorb
    # (polymorph-js produced NaNs here), pad at the final endpoint
    while total_needed > 0:
        result.extend((dx, dy, dx, dy, dx, dy))
        total_needed -= 6
    return result


def fill_points(matrix: list[list[list[float]]], add_points: int) -> None:
    """Equalize point counts between paired subpaths (in place)."""
    left_segments, right_segments = matrix
    for i in range(len(left_segments)):
        left = left_segments[i]
        right = right_segments[i]
        total_length = max(len(left), len(right)) + add_points
        left_segments[i] = fill_subpath(left, total_length)
        right_segments[i] = fill_subpath(right, total_length)


def rotate_points(ns: list[float], count: int) -> None:
    """Rotate a flat point buffer left by count elements (in place)."""
    ns[:] = ns[count:] + ns[:count]


def normalize_points(absolute: bool, origin_x: float, origin_y: float, ns: list[float]) -> None:
    """Rotate a closed subpath's draw order to start nearest the origin (in place).

    Open subpaths are left untouched. Note: like polymorph-js, the nearest-point
    scan compares each curve's first control point rather than its endpoint —
    an approximation that works because control points sit near their curve.
    """
    if ns[-2] != ns[0] or ns[-1] != ns[1]:
        return

    if not absolute:
        origin_x, origin_y = compute_absolute_origin(origin_x, origin_y, ns)

    buffer = ns[2:]
    index = 0
    min_amount: float | None = None
    for i in range(0, len(buffer), 6):
        amount = distance(origin_x, origin_y, buffer[i], buffer[i + 1])
        if min_amount is None or amount < min_amount:
            min_amount = amount
            index = i

    rotate_points(buffer, index)

    # the new start position is the endpoint of the (rotated) last curve
    ns[0] = buffer[-2]
    ns[1] = buffer[-1]
    ns[2:] = buffer


def normalize_paths(
    left: list[list[float]],
    right: list[list[float]],
    *,
    optimize: str = "fill",
    origin: Origin = Origin(0.0, 0.0),
    add_points: int = 0,
) -> list[list[list[float]]]:
    """Produce an aligned [left, right] matrix ready for elementwise mixing.

    Inputs are deep-copied, so Path data is never mutated and paths can be
    reused across multiple interpolators.
    """
    left = [list(segment) for segment in left]
    right = [list(segment) for segment in right]

    if optimize == "fill":
        left = sorted_segments(left)
        right = sorted_segments(right)

    if len(left) != len(right):
        if optimize == "fill":
            fill_segments(left, right, origin)
        else:
            raise ValueError("optimize='none' requires paths with equal subpath counts")

    matrix = [left, right]
    if optimize == "fill":
        for i in range(len(left)):
            normalize_points(origin.absolute, origin.x, origin.y, left[i])
            normalize_points(origin.absolute, origin.x, origin.y, right[i])
        fill_points(matrix, add_points * 6)
    else:
        for left_segment, right_segment in zip(left, right):
            if len(left_segment) != len(right_segment):
                raise ValueError("optimize='none' requires subpaths with equal point counts")
    return matrix
