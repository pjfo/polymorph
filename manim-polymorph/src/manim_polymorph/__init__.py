"""manim-polymorph: polymorph SVG path morphing as a ManimCE plugin."""

from polymorph import Origin

from .animation import Polymorph, PolymorphTransform
from .mobject import SVGPathVMobject, svg_path_mobject, svg_path_mobjects

__all__ = [
    "Origin",
    "Polymorph",
    "PolymorphTransform",
    "SVGPathVMobject",
    "svg_path_mobject",
    "svg_path_mobjects",
]

__version__ = "0.1.0"
