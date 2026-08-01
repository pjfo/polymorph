"""A small five-pointed star morphs into the star that contains it,
two ways at once: Manim's built-in Transform on the left, polymorph
on the right (via the manim-polymorph plugin).

The inner star is rotated 36 degrees so its points rest in the outer
star's troughs. A generic point-interpolating Transform rotates the
shape into place. With polymorph the vertex pairing is yours to
choose: order both paths from the same angle and the star's points
stay pinned while its troughs erupt outward.

Render with Manim Community (pip install manim manim-polymorph):

    manim -qm --fps 30 examples/star_morph.py StarMorph
"""

import math

from manim import DOWN, LEFT, RIGHT, WHITE, Scene, Text, Transform, rate_functions
from manim_polymorph import Polymorph, svg_path_mobjects

TEAL = "#2BC3D2"
INK = "#0E1418"
SIDE = 3.55  # half-screen offset

# trough/point radius ratio of a regular pentagram
PENTAGRAM = math.sin(math.radians(18)) / math.sin(math.radians(54))

STYLE = {"stroke_color": TEAL, "stroke_width": 5, "fill_color": TEAL, "fill_opacity": 0.35}
GUIDE = {"stroke_color": WHITE, "stroke_opacity": 0.25, "stroke_width": 2, "fill_opacity": 0.0}


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


class StarMorph(Scene):
    def construct(self):
        self.camera.background_color = INK

        # inner point radius == outer trough radius, so the inner star's
        # points sit exactly in the outer star's troughs
        inner = star_path(45 * PENTAGRAM, rotation=math.pi / 5)
        outer = star_path(45)
        # the same outer star, re-ordered to list its vertices from the same
        # angle as the inner one: with optimize="none" vertex k morphs to
        # vertex k, giving pinned points and no twist
        outer_aligned = star_path(45, rotation=math.pi / 5, trough_first=True)

        # one shared coordinate mapping for every keyframe, so shapes keep
        # their relative sizes and the morphs cannot jump
        inner_mob, outer_mob, aligned_mob, guide_mob = svg_path_mobjects(
            [inner, outer, outer_aligned, outer],
            height=4.1,
            styles=[STYLE, STYLE, STYLE, GUIDE],
        )

        manim_star = inner_mob.copy().shift(LEFT * SIDE)
        manim_target = outer_mob.copy().shift(LEFT * SIDE)
        poly_star = inner_mob.copy().shift(RIGHT * SIDE)
        poly_target = aligned_mob.copy().shift(RIGHT * SIDE)

        for side, name in ((LEFT, "Manim Transform"), (RIGHT, "polymorph")):
            self.add(guide_mob.copy().shift(side * SIDE))
            self.add(
                Text(name, font="monospace", font_size=24, color=WHITE, fill_opacity=0.6)
                .shift(side * SIDE + DOWN * 3.1)
            )
        self.add(manim_star, poly_star)

        self.wait(0.75)
        self.play(
            Transform(manim_star, manim_target),
            Polymorph(poly_star, poly_target, optimize="none"),
            run_time=4,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.wait(1.25)
