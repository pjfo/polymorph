"""Demo scene for manim-polymorph.

Render with:

    manim -pql manim-polymorph/examples/demo.py PolymorphDemo
"""

from manim import BLUE, RED, WHITE, YELLOW, Scene, smooth

from manim_polymorph import Polymorph, svg_path_mobjects

# a heart drawn with arcs and quadratics (exercises polymorph's arc converter)
HEART = (
    "M50 88 Q10 55 4 36 A23 23 0 0 1 50 24 A23 23 0 0 1 96 36 Q90 55 50 88 Z"
)

# a five-point star made of straight lines (exercises start-point rotation)
STAR = (
    "M50 6 L61 38 L95 38 L67 58 L78 92 L50 71 L22 92 L33 58 L5 38 L39 38 Z"
)

# a ring: outer blob plus an inner hole, two subpaths (exercises subpath filling)
RING = (
    "M50 10 C75 10 92 28 92 50 C92 72 75 90 50 90 C25 90 8 72 8 50 C8 28 25 10 50 10 Z "
    "M50 32 C61 32 70 40 70 50 C70 60 61 68 50 68 C39 68 30 60 30 50 C30 40 39 32 50 32 Z"
)


class PolymorphDemo(Scene):
    def construct(self):
        heart, star, ring = svg_path_mobjects(
            [HEART, STAR, RING],
            height=4,
            styles=[
                {"fill_color": RED},
                {"fill_color": YELLOW, "stroke_color": WHITE, "stroke_width": 2},
                {"fill_color": BLUE},
            ],
        )

        shape = heart.copy()
        self.add(shape)
        self.wait(0.3)

        # simple two-shape morph with style crossfade
        self.play(Polymorph(shape, star, run_time=2, rate_func=smooth))
        self.wait(0.3)

        # multi-keyframe sequence morphing through the ring and back to the
        # heart; fill_mode="grow" makes the ring's extra subpath grow from
        # the shape's center instead of splitting off a clone (the default)
        self.play(
            Polymorph(shape, ring, heart, run_time=4, fill_mode="grow", origin=(0.5, 0.5))
        )
        self.wait(0.5)
