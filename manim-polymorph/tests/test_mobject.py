"""Tests for d-string -> VMobject construction. Requires manim."""

import numpy as np
import pytest

manim = pytest.importorskip("manim")

from manim_polymorph.mobject import (
    SVGPathVMobject,
    svg_path_mobject,
    svg_path_mobjects,
)

SQUARE_10 = "M0 0 L10 0 L10 10 L0 10 Z"
SQUARE_20 = "M0 0 L20 0 L20 20 L0 20 Z"


def test_height_fit_and_centering():
    mob = svg_path_mobject(SQUARE_10, height=3.0)
    assert mob.height == pytest.approx(3.0)
    assert np.allclose(mob.get_center(), [0, 0, 0], atol=1e-9)


def test_width_fit():
    mob = svg_path_mobject("M0 0 L10 0 L10 5 L0 5 Z", height=None, width=4.0)
    assert mob.width == pytest.approx(4.0)
    assert mob.height == pytest.approx(2.0)


def test_raw_units_when_unsized():
    mob = svg_path_mobject(SQUARE_10, height=None, center=False)
    assert mob.width == pytest.approx(10.0)


def test_y_flip():
    # in SVG, larger y is further down; in the scene it must be further down too,
    # i.e. at smaller scene y
    mob = svg_path_mobject("M0 0 L10 0 L10 10 L0 10 Z", height=None, center=False)
    ys = mob.points[:, 1]
    assert ys.min() == pytest.approx(-10.0)
    assert ys.max() == pytest.approx(0.0)


def test_style_kwargs():
    mob = svg_path_mobject(
        SQUARE_10, fill_color=manim.RED, fill_opacity=0.5, stroke_color=manim.BLUE, stroke_width=2
    )
    assert mob.get_fill_color().to_hex() == manim.RED.to_hex()
    assert mob.get_fill_opacity() == pytest.approx(0.5)
    assert mob.get_stroke_color().to_hex() == manim.BLUE.to_hex()
    assert mob.get_stroke_width() == pytest.approx(2)


def test_shared_mapping_preserves_relative_size_and_offset():
    small, big = svg_path_mobjects([SQUARE_10, SQUARE_20], height=4.0)
    assert big.width / small.width == pytest.approx(2.0)
    assert big.height == pytest.approx(4.0)  # big square spans the union bbox
    # both squares share the top-left corner in SVG space; after the shared
    # y-flip affine that corner must coincide in scene space
    small_corner = small.points[0]
    big_corner = big.points[0]
    assert np.allclose(small_corner, big_corner)


def test_per_shape_styles():
    a, b = svg_path_mobjects(
        [SQUARE_10, SQUARE_20],
        fill_opacity=0.25,
        styles=[{"fill_color": manim.RED}, {"fill_color": manim.BLUE}],
    )
    assert a.get_fill_color().to_hex() == manim.RED.to_hex()
    assert b.get_fill_color().to_hex() == manim.BLUE.to_hex()
    assert a.get_fill_opacity() == pytest.approx(0.25)
    assert b.get_fill_opacity() == pytest.approx(0.25)


def test_styles_length_mismatch():
    with pytest.raises(ValueError):
        svg_path_mobjects([SQUARE_10], styles=[{}, {}])


def test_empty_input():
    with pytest.raises(ValueError):
        svg_path_mobjects([])


def test_opengl_renderer_rejected(opengl_renderer):
    with opengl_renderer(), pytest.raises(NotImplementedError):
        SVGPathVMobject(SQUARE_10)
