"""A small five-pointed star morphs into the star that contains it,
two ways at once: Manim's built-in Transform on the left, polymorph
on the right.

The inner star is rotated 36 degrees so its points rest in the outer
star's troughs. A generic point-interpolating Transform rotates the
shape into place. With polymorph the vertex pairing is yours to
choose: order both paths from the same angle and the star's points
stay pinned while its troughs erupt outward.

polymorph's parsed data is cubic beziers -- the same primitive Manim's
VMobject uses -- so mixed coordinates map straight onto the screen.

Render with Manim Community (pip install manim):

    manim -qm --fps 30 examples/star_morph.py StarMorph
"""

import math

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    WHITE,
    Scene,
    Text,
    Transform,
    ValueTracker,
    VMobject,
    always_redraw,
    rate_functions,
)

from polymorph import mix_points, parse_points
from polymorph.normalize import normalize_paths

TEAL = "#2BC3D2"
INK = "#0E1418"
SCALE = 20  # SVG units per scene unit
SIDE = 3.55  # half-screen offset

# trough/point radius ratio of a regular pentagram
PENTAGRAM = math.sin(math.radians(18)) / math.sin(math.radians(54))

STYLE = {"stroke_color": TEAL, "stroke_width": 5, "fill_color": TEAL, "fill_opacity": 0.35}
GUIDE = {"stroke_color": WHITE, "stroke_opacity": 0.25, "stroke_width": 2}


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
        outer = star_path(45)

        # left: Manim's Transform between the two paths as-authored
        manim_star = vmobject_from_segments(parse_points(inner), **STYLE).shift(LEFT * SIDE)
        manim_target = vmobject_from_segments(parse_points(outer), **STYLE).shift(LEFT * SIDE)

        # right: polymorph, with the outer path re-ordered to start from the
        # same angle as the inner one, so with optimize="none" vertex k morphs
        # to vertex k: pinned points, no twist
        outer_aligned = star_path(45, rotation=math.pi / 5, trough_first=True)
        left, right = normalize_paths(
            parse_points(inner), parse_points(outer_aligned), optimize="none"
        )
        t = ValueTracker(0.0)
        poly_star = always_redraw(
            lambda: vmobject_from_segments(
                [mix_points(a, b, t.get_value()) for a, b in zip(left, right)], **STYLE
            ).shift(RIGHT * SIDE)
        )

        for side in (LEFT, RIGHT):
            guide = vmobject_from_segments(parse_points(outer), **GUIDE).shift(side * SIDE)
            label = Text(
                "Manim Transform" if side is LEFT else "polymorph",
                font="monospace", font_size=24, color=WHITE, fill_opacity=0.6,
            ).shift(side * SIDE + DOWN * 3.1)
            self.add(guide, label)
        self.add(manim_star, poly_star)

        self.wait(0.75)
        self.play(
            Transform(manim_star, manim_target),
            t.animate.set_value(1.0),
            run_time=4,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.wait(1.25)
