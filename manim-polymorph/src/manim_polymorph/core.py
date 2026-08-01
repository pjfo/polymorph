"""Numeric bridge between polymorph poly-bezier data and Manim point arrays.

This module deliberately does not import manim: it only converts between
polymorph's flat per-subpath coordinate lists and the (N, 3) cubic bezier
point arrays that Manim's Cairo-renderer VMobjects use, and drives the
morph numerically so no SVG strings are rendered or parsed per frame.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from itertools import pairwise

import numpy as np
from polymorph.normalize import Origin, normalize_paths

DEFAULT_ORIGIN = Origin(0.0, 0.0)

__all__ = [
    "NumericMorph",
    "manim_subpaths_to_polymorph_data",
    "polymorph_data_to_manim_points",
    "subpath_to_manim_points",
]


def subpath_to_manim_points(ns: Sequence[float]) -> np.ndarray:
    """Convert one flat polymorph subpath to a (4k, 3) Manim cubic point array.

    polymorph stores a subpath as [mx, my, h0x, h0y, h1x, h1y, ax, ay, ...]:
    a moveto followed by k cubic curves of two handles and an end anchor.
    Manim wants groups of four points [a0, h0, h1, a1] per curve, with the
    shared anchor duplicated between consecutive curves. z is left at 0.
    """
    arr = np.asarray(ns, dtype=np.float64)
    if len(arr) < 8 or (len(arr) - 2) % 6 != 0:
        raise ValueError(f"subpath must have 2 + 6k coordinates with k >= 1, got {len(arr)}")
    k = (len(arr) - 2) // 6
    curves = arr[2:].reshape(k, 6)
    pts = np.zeros((4 * k, 3))
    pts[0, :2] = arr[:2]
    pts[4::4, :2] = curves[:-1, 4:6]
    pts[1::4, :2] = curves[:, 0:2]
    pts[2::4, :2] = curves[:, 2:4]
    pts[3::4, :2] = curves[:, 4:6]
    return pts


def polymorph_data_to_manim_points(data: Sequence[Sequence[float]]) -> np.ndarray:
    """Convert polymorph path data (list of flat subpaths) to one point array.

    Manim detects subpath boundaries by discontinuity between the end anchor
    of one curve and the start anchor of the next, so plain concatenation is
    the correct join.
    """
    if not data:
        return np.zeros((0, 3))
    return np.concatenate([subpath_to_manim_points(ns) for ns in data])


def manim_subpaths_to_polymorph_data(
    subpaths: Iterable[np.ndarray], *, close_tol: float = 1e-6
) -> list[list[float]]:
    """Convert Manim subpath point arrays back to polymorph's flat lists.

    Accepts the output of VMobject.get_subpaths(): each subpath is a (4m, 3)
    array of cubic control points. Closed subpaths are snapped exactly shut
    when the endpoint is within close_tol of the start, because polymorph
    detects closure by exact coordinate equality (normalize.py) and float
    drift would silently disable its start-point rotation.
    """
    data: list[list[float]] = []
    for sp in subpaths:
        sp = np.asarray(sp, dtype=np.float64)
        if len(sp) == 0:
            continue
        if len(sp) % 4 != 0:
            raise ValueError(f"subpath length must be a multiple of 4, got {len(sp)}")
        flat = [float(sp[0, 0]), float(sp[0, 1])]
        for j in range(0, len(sp), 4):
            for p in (sp[j + 1], sp[j + 2], sp[j + 3]):
                flat.append(float(p[0]))
                flat.append(float(p[1]))
        if math.hypot(flat[-2] - flat[0], flat[-1] - flat[1]) < close_tol:
            flat[-2] = flat[0]
            flat[-1] = flat[1]
        data.append(flat)
    return data


class NumericMorph:
    """Morph between keyframe paths entirely on numpy point arrays.

    keyframes: two or more polymorph path datas (each a list of flat
    subpath coordinate lists). Consecutive pairs are aligned once with
    polymorph's normalize_paths; per frame the aligned endpoints are mixed
    with a single vectorized lerp, so t=0 and t=1 have exactly the same
    point structure as every interior frame (no polymorph string
    short-circuit, no coordinate rounding).
    """

    def __init__(
        self,
        keyframes: Sequence[Sequence[Sequence[float]]],
        *,
        optimize: str = "fill",
        origin: Origin = DEFAULT_ORIGIN,
        add_points: int = 0,
    ) -> None:
        if len(keyframes) < 2:
            raise ValueError("at least two keyframes are required")
        self._segments: list[tuple[np.ndarray, np.ndarray]] = []
        for left, right in pairwise(keyframes):
            matrix = normalize_paths(
                [list(ns) for ns in left],
                [list(ns) for ns in right],
                optimize=optimize,
                origin=origin,
                add_points=add_points,
            )
            self._segments.append(
                (
                    polymorph_data_to_manim_points(matrix[0]),
                    polymorph_data_to_manim_points(matrix[1]),
                )
            )

    @property
    def num_segments(self) -> int:
        return len(self._segments)

    def segment_of(self, t: float) -> tuple[int, float]:
        """Map t in [0, 1] to (segment index, local offset).

        The index is clamped to a valid segment; the local offset is left
        unclamped so overshooting rate functions extrapolate smoothly.
        """
        d = len(self._segments) * t
        h = min(max(math.floor(d), 0), len(self._segments) - 1)
        return h, d - h

    def points_at(self, t: float) -> np.ndarray:
        """Return the (M, 3) Manim point array for morph position t."""
        h, s = self.segment_of(t)
        left, right = self._segments[h]
        return left + (right - left) * s
