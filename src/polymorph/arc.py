"""Convert SVG elliptical arcs to cubic bezier curves.

Port of the classic Raphael.js arc-to-curve algorithm used by polymorph-js.
"""

from __future__ import annotations

import math

_120 = math.pi * 120 / 180
_2PI = math.pi * 2


def arc_to_curve(
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    angle: float,
    large: float,
    sweep: float,
    dx: float,
    dy: float,
) -> list[float]:
    """Convert one elliptical arc to a flat list of cubic bezier 6-tuples.

    Arguments follow the SVG A command: start point (x1, y1), radii, x-axis
    rotation in degrees, large-arc and sweep flags, and end point (dx, dy).
    Arcs with non-positive radii degrade to a straight line, as in SVG.
    """
    return _arc_to_curve(x1, y1, rx, ry, angle, large, sweep, dx, dy, 0.0, 0.0, 0.0, 0.0, False)


def _arc_to_curve(
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    angle: float,
    large: float,
    sweep: float,
    dx: float,
    dy: float,
    f1: float,
    f2: float,
    cx: float,
    cy: float,
    recursive: bool,
) -> list[float]:
    if rx <= 0 or ry <= 0:
        return [x1, y1, dx, dy, dx, dy]

    rad = math.pi / 180 * angle
    cosrad = math.cos(rad)
    sinrad = math.sin(rad)

    if not recursive:
        # De-rotate the endpoints so the ellipse is axis-aligned.
        x1old = x1
        dxold = dx
        x1 = x1old * cosrad - y1 * -sinrad
        y1 = x1old * -sinrad + y1 * cosrad
        dx = dxold * cosrad - dy * -sinrad
        dy = dxold * -sinrad + dy * cosrad

        x = (x1 - dx) / 2
        y = (y1 - dy) / 2

        # Scale up radii that are too small to span the endpoints.
        h = x * x / (rx * rx) + y * y / (ry * ry)
        if h > 1:
            h = math.sqrt(h)
            rx = h * rx
            ry = h * ry

        k = (-1 if large == sweep else 1) * math.sqrt(
            abs(
                (rx * rx * ry * ry - rx * rx * y * y - ry * ry * x * x)
                / (rx * rx * y * y + ry * ry * x * x)
            )
        )

        cx = k * rx * y / ry + (x1 + dx) / 2
        cy = k * -ry * x / rx + (y1 + dy) / 2

        f1 = math.asin((y1 - cy) / ry)
        f2 = math.asin((dy - cy) / ry)

        if x1 < cx:
            f1 = math.pi - f1
        if dx < cx:
            f2 = math.pi - f2
        if f1 < 0:
            f1 += _2PI
        if f2 < 0:
            f2 += _2PI
        if sweep and f1 > f2:
            f1 -= _2PI
        if not sweep and f2 > f1:
            f2 -= _2PI

    if abs(f2 - f1) > _120:
        # Sweep is too large for one bezier; split off a 120-degree slice and recurse.
        f2old = f2
        x2old = dx
        y2old = dy

        f2 = f1 + _120 * (1 if sweep and f2 > f1 else -1)
        dx = cx + rx * math.cos(f2)
        dy = cy + ry * math.sin(f2)
        res = _arc_to_curve(dx, dy, rx, ry, angle, 0, sweep, x2old, y2old, f2, f2old, cx, cy, True)
    else:
        res = []

    t = 4 / 3 * math.tan((f2 - f1) / 4)

    res[0:0] = [
        2 * x1 - (x1 + t * rx * math.sin(f1)),
        2 * y1 - (y1 - t * ry * math.cos(f1)),
        dx + t * rx * math.sin(f2),
        dy - t * ry * math.cos(f2),
        dx,
        dy,
    ]

    if not recursive:
        # Rotate the whole curve back into position.
        for i in range(0, len(res), 2):
            xt = res[i]
            yt = res[i + 1]
            res[i] = xt * cosrad - yt * sinrad
            res[i + 1] = xt * sinrad + yt * cosrad

    return res
