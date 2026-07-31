"""polymorph: morph SVG paths in pure Python.

A Python port of polymorph-js (https://github.com/notoriousb1t/polymorph).
"""

from .interpolate import interpolate, mix_points
from .normalize import Origin
from .parse import parse_points
from .path import Path
from .render import js_round, make_formatter, render_path

__version__ = "2.0.0"

__all__ = [
    "Origin",
    "Path",
    "interpolate",
    "js_round",
    "make_formatter",
    "mix_points",
    "parse_points",
    "render_path",
    "__version__",
]
