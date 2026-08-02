"""Tests for the Polymorph animation, driven without a Scene. Requires manim."""

import numpy as np
import pytest

manim = pytest.importorskip("manim")

from manim_polymorph import Polymorph, svg_path_mobjects

HEART = (
    "M10 4 C10 2 8.5 1 7 1 C5.8 1 4.6 1.6 4 2.6 C3.4 1.6 2.2 1 1 1 "
    "C-0.5 1 -2 2 -2 4 C-2 7 4 11 4 11 C4 11 10 7 10 4 Z"
)
STAR = "M5 0 L6.2 3.4 L10 3.4 L7 5.6 L8.1 9 L5 7 L1.9 9 L3 5.6 L0 3.4 L3.8 3.4 Z"


def make_pair(**style):
    return svg_path_mobjects([HEART, STAR], height=3, **style)


def test_no_pop_at_endpoints():
    # the regression polymorph's t=0/1 string short-circuit would cause
    heart, star = make_pair()
    anim = Polymorph(heart, star, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(0.0)
    at_zero = heart.points.copy()
    anim.interpolate(1e-6)
    assert np.abs(heart.points - at_zero).max() < 1e-3
    anim.interpolate(1.0)
    at_one = heart.points.copy()
    anim.interpolate(1 - 1e-6)
    assert np.abs(heart.points - at_one).max() < 1e-3


def test_rate_func_is_applied():
    # interpolate_mobject receives raw alpha; a constant-zero rate function
    # must pin the start shape at every alpha
    heart, star = make_pair()
    anim = Polymorph(heart, star, rate_func=lambda a: 0.0)
    anim.begin()
    anim.interpolate(0.0)
    start = heart.points.copy()
    anim.interpolate(0.7)
    assert np.allclose(heart.points, start)


def test_shape_actually_morphs():
    heart, star = make_pair()
    star_points_before = star.points.copy()
    anim = Polymorph(heart, star, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(0.0)
    start = heart.points.copy()
    anim.interpolate(0.5)
    assert not np.allclose(heart.points, start)
    # the target itself must never be mutated
    assert np.array_equal(star.points, star_points_before)


def test_style_crossfade_midpoint():
    heart, star = make_pair(styles=[{"fill_color": manim.PURE_RED}, {"fill_color": manim.PURE_BLUE}])
    anim = Polymorph(heart, star, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(0.5)
    rgb = heart.get_fill_color().to_rgb()
    assert rgb[0] == pytest.approx(0.5, abs=0.05)
    assert rgb[2] == pytest.approx(0.5, abs=0.05)


def test_crossfade_disabled_keeps_style():
    heart, star = make_pair(styles=[{"fill_color": manim.PURE_RED}, {"fill_color": manim.PURE_BLUE}])
    anim = Polymorph(heart, star, crossfade_style=False, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(0.5)
    assert heart.get_fill_color().to_hex() == manim.PURE_RED.to_hex()


def test_finish_snaps_to_target():
    heart, star = make_pair(styles=[{"fill_color": manim.PURE_RED}, {"fill_color": manim.PURE_BLUE}])
    anim = Polymorph(heart, star, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(1.0)
    anim.finish()
    assert len(heart.points) == len(star.points)
    assert np.allclose(heart.points, star.points)
    assert heart.get_fill_color().to_hex() == manim.PURE_BLUE.to_hex()


def test_multi_target_sequencing():
    heart, star = make_pair()
    third = star.copy().shift(manim.RIGHT)
    anim = Polymorph(heart, star, third, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(0.5)  # end of first segment / start of second
    mid = heart.points.copy()
    anim.interpolate(1.0)
    assert anim._morph.num_segments == 2
    assert not np.allclose(mid, heart.points)


def test_fill_mode_passes_through():
    heart, star = make_pair()
    pair_target = manim.VGroup(star.copy(), star.copy().shift(manim.RIGHT * 4))

    share = Polymorph(heart.copy(), pair_target, rate_func=manim.linear)
    share.begin()
    share.interpolate(0.0)
    pts = share.mobject.points
    first, second = pts[: len(pts) // 2], pts[len(pts) // 2 :]
    # both subpaths start as the same full heart — no degenerate filler
    assert np.allclose(first, second)
    assert np.ptp(second[:, :2], axis=0).min() > 0

    grow = Polymorph(heart.copy(), pair_target, fill_mode="grow", rate_func=manim.linear)
    grow.begin()
    grow.interpolate(0.0)
    spans = [np.ptp(sp[:, :2], axis=0).max() for sp in grow.mobject.get_subpaths()]
    assert min(spans) == 0  # the filler subpath starts collapsed at the origin


def test_str_target_rejected():
    heart, _ = make_pair()
    with pytest.raises(TypeError, match="svg_path_mobjects"):
        Polymorph(heart, "M0 0 L1 0 L1 1 Z")


def test_zero_targets_rejected():
    heart, _ = make_pair()
    with pytest.raises(ValueError):
        Polymorph(heart)


def test_group_source_is_flattened():
    heart, star = make_pair()
    group = manim.VGroup(heart.copy(), star.copy())
    target = heart.copy().shift(manim.RIGHT)
    anim = Polymorph(group, target, rate_func=manim.linear)
    anim.begin()
    # the family collapses onto the parent for the duration of the morph
    assert group.submobjects == []
    assert len(group.points) > 0
    anim.interpolate(1.0)
    anim.finish()
    assert np.allclose(group.points, target.points)


def test_structured_target_restored_on_finish():
    heart, star = make_pair()
    group_target = manim.VGroup(heart.copy(), star.copy().shift(manim.RIGHT))
    source = heart.copy()
    anim = Polymorph(source, group_target, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(1.0)
    anim.finish()
    # the target's submobject structure comes back, geometry intact
    got = [m.points for m in source.family_members_with_points()]
    want = [m.points for m in group_target.family_members_with_points()]
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert np.allclose(g, w)


def test_text_morphs_and_crossfades():
    text = manim.Text("Hi", fill_color=manim.PURE_RED, fill_opacity=1.0)
    heart, _ = make_pair(styles=[{"fill_color": manim.PURE_BLUE}, {}])
    anim = Polymorph(text, heart, rate_func=manim.linear)
    anim.begin()
    assert text.submobjects == []
    anim.interpolate(0.0)
    start = text.points.copy()
    assert len(start) > 0
    anim.interpolate(0.5)
    assert not np.allclose(text.points, start)
    # style rides the first glyph's fill, crossfading toward the target
    rgb = text.get_fill_color().to_rgb()
    assert rgb[0] == pytest.approx(0.5, abs=0.05)
    assert rgb[2] == pytest.approx(0.5, abs=0.05)


def test_text_target_keeps_glyphs():
    heart, _ = make_pair()
    text = manim.Text("Hi")
    anim = Polymorph(heart, text, rate_func=manim.linear)
    anim.begin()
    anim.interpolate(1.0)
    anim.finish()
    got = [m.points for m in heart.family_members_with_points()]
    want = [m.points for m in text.family_members_with_points()]
    assert len(got) == len(want) == 2
    for g, w in zip(got, want):
        assert np.allclose(g, w)


def test_opengl_renderer_rejected(opengl_renderer):
    heart, star = make_pair()
    anim = Polymorph(heart, star)
    with opengl_renderer(), pytest.raises(NotImplementedError):
        anim.begin()
