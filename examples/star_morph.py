"""A small five-pointed star morphs into the star that contains it.

The inner star is rotated 36 degrees so its points rest in the outer
star's troughs. Vertices are paired so those points stay pinned while
the inner troughs erupt outward into the big star's points.

polymorph's parsed data is cubic beziers -- the same primitive Manim's
VMobject uses -- so mixed coordinates map straight onto the screen.

Render with Manim Community (pip install manim):

    manim -qm --fps 30 examples/star_morph.py StarMorph
"""

import math

import numpy as np
from manim import WHITE, Scene, ValueTracker, VMobject, always_redraw, rate_functions

from polymorph import mix_points, parse_points
from polymorph.normalize import normalize_paths

TEAL = "#2BC3D2"
INK = "#0E1418"
SCALE = 15  # SVG units per scene unit

# trough/point radius ratio of a regular pentagram
PENTAGRAM = math.sin(math.radians(18)) / math.sin(math.radians(54))


def star_path(point_radius, rotation=0.0, trough_first=False):
    """Five-pointed star centered at (50, 50) in a 100x100 SVG space."""
    radii = (point_radius, point_radius * PENTAGRAM)
    if trough_first:
        radii = radii[::-1]
    vertices = []
    for i in range(10):
        angle = -math.pi / 2 + rotation + i * math.pi / 5
        vertices.append(
            (50 + radii[i % 2] * math.cos(angle), 50 + radii[i % 2] * math.sin(angle))
        )
    return "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in vertices) + " Z"


def to_scene(x, y):
    return np.array([(x - 50) / SCALE, (50 - y) / SCALE, 0.0])


def vmobject_from_segments(segments, **style):
    mobject = VMobject(**style)
    for n in segments:
        mobject.start_new_path(to_scene(n[0], n[1]))
        for i in range(2, len(n), 6):
            mobject.add_cubic_bezier_curve_to(
                to_scene(n[i], n[i + 1]),
                to_scene(n[i + 2], n[i + 3]),
                to_scene(n[i + 4], n[i + 5]),
            )
    return mobject


class StarMorph(Scene):
    def construct(self):
        self.camera.background_color = INK

        # inner point radius == outer trough radius, so the inner star's
        # points sit exactly in the outer star's troughs
        inner = star_path(45 * PENTAGRAM, rotation=math.pi / 5)
        outer = star_path(45, rotation=math.pi / 5, trough_first=True)

        # both paths list their vertices from the same angle, so with
        # optimize="none" vertex k morphs to vertex k: pinned points, no twist
        left, right = normalize_paths(parse_points(inner), parse_points(outer), optimize="none")

        guide = vmobject_from_segments(
            parse_points(star_path(45)), stroke_color=WHITE, stroke_opacity=0.25, stroke_width=2
        )
        t = ValueTracker(0.0)
        morph = always_redraw(
            lambda: vmobject_from_segments(
                [mix_points(a, b, t.get_value()) for a, b in zip(left, right)],
                stroke_color=TEAL,
                stroke_width=5,
                fill_color=TEAL,
                fill_opacity=0.35,
            )
        )

        self.add(guide, morph)
        self.wait(0.75)
        self.play(t.animate.set_value(1.0), run_time=4, rate_func=rate_functions.ease_in_out_sine)
        self.wait(1.25)
