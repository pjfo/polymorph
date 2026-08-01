"""Build styled Manim VMobjects directly from SVG path d-strings."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from manim import WHITE, VMobject, config
from manim.constants import RendererType
from manim.mobject.opengl.opengl_compatibility import ConvertToOpenGL
from polymorph import parse_points

from .core import polymorph_data_to_manim_points

__all__ = ["SVGPathVMobject", "svg_path_mobject", "svg_path_mobjects"]


def _ensure_cairo_cubics() -> None:
    """manim-polymorph only supports the Cairo renderer's 4-point cubics."""
    if config.renderer is RendererType.OPENGL:
        raise NotImplementedError(
            "manim-polymorph supports the Cairo renderer only (4-point cubic "
            "VMobjects); the OpenGL renderer uses 3-point quadratics"
        )


def _d_string_to_points(d: str) -> np.ndarray:
    """Parse a d-string into Manim points in SVG coordinates with y negated.

    SVG is y-down and Manim scenes are y-up; negating y here keeps the whole
    SVG-to-scene mapping a single fixed affine transform.
    """
    pts = polymorph_data_to_manim_points(parse_points(d))
    pts[:, 1] *= -1
    return pts


class SVGPathVMobject(VMobject, metaclass=ConvertToOpenGL):
    """A VMobject built from an SVG path d-string.

    The path is parsed with polymorph (no svgelements round-trip), flipped to
    Manim's y-up convention, then optionally scaled to a target height or
    width and centered. With both height and width None the shape keeps raw
    SVG user units.
    """

    def __init__(
        self,
        d: str,
        *,
        height: float | None = 2.0,
        width: float | None = None,
        center: bool = True,
        fill_color: Any = WHITE,
        fill_opacity: float = 1.0,
        stroke_color: Any = None,
        stroke_width: float = 0.0,
        **kwargs: Any,
    ) -> None:
        _ensure_cairo_cubics()
        self._d = d
        super().__init__(
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            **kwargs,
        )
        self.set_points(_d_string_to_points(d))
        if height is not None:
            self.scale_to_fit_height(height)
        elif width is not None:
            self.scale_to_fit_width(width)
        if center:
            self.center()


def svg_path_mobject(d: str, **kwargs: Any) -> SVGPathVMobject:
    """Build a single styled VMobject from an SVG path d-string."""
    return SVGPathVMobject(d, **kwargs)


def svg_path_mobjects(
    ds: Sequence[str],
    *,
    height: float = 2.0,
    center: bool = True,
    styles: Sequence[dict[str, Any]] | None = None,
    **common_style: Any,
) -> list[SVGPathVMobject]:
    """Build one VMobject per d-string under a single shared coordinate mapping.

    One affine transform (uniform scale, y-flip, translation) is computed from
    the union bounding box of all paths in SVG user space, sized so the union
    fits `height` scene units, then applied identically to every shape. The
    shapes therefore keep their relative sizes and positions — which is what
    makes morphing between them stable: the mapping cannot change mid-morph.

    styles: optional per-shape style dicts merged over the common style kwargs.
    """
    if not ds:
        raise ValueError("at least one d-string is required")
    if styles is not None and len(styles) != len(ds):
        raise ValueError(f"styles must have one entry per path ({len(ds)}), got {len(styles)}")

    all_points = [_d_string_to_points(d) for d in ds]
    union = np.concatenate(all_points)
    mins = union.min(axis=0)
    maxs = union.max(axis=0)
    union_height = maxs[1] - mins[1]
    scale = height / union_height if union_height > 0 else 1.0
    shift = -(mins + maxs) / 2 if center else np.zeros(3)

    mobjects = []
    for d, pts in zip(ds, all_points):
        style = dict(common_style)
        if styles is not None:
            style.update(styles[len(mobjects)])
        mob = SVGPathVMobject(d, height=None, width=None, center=False, **style)
        mob.set_points((pts + shift) * scale)
        mobjects.append(mob)
    return mobjects
