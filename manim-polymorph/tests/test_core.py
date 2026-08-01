"""Tests for the numeric conversion layer. These do not require manim."""

import numpy as np
import pytest
from polymorph import parse_points

from manim_polymorph.core import (
    NumericMorph,
    manim_subpaths_to_polymorph_data,
    polymorph_data_to_manim_points,
    subpath_to_manim_points,
)

SQUARE = "M0 0 L10 0 L10 10 L0 10 Z"
CIRCLE = "M50 25 A25 25 0 1 1 0 25 A25 25 0 1 1 50 25 Z"


def test_subpath_layout_and_anchor_duplication():
    # one moveto plus two cubic curves
    ns = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]
    pts = subpath_to_manim_points(ns)
    assert pts.shape == (8, 3)
    assert np.array_equal(pts[0], [0, 0, 0])  # start anchor
    assert np.array_equal(pts[1], [1, 1, 0])  # handle 1
    assert np.array_equal(pts[2], [2, 2, 0])  # handle 2
    assert np.array_equal(pts[3], [3, 3, 0])  # end anchor
    assert np.array_equal(pts[4], [3, 3, 0])  # duplicated as next start anchor
    assert np.array_equal(pts[7], [6, 6, 0])
    assert np.all(pts[:, 2] == 0)


def test_subpath_rejects_bad_lengths():
    with pytest.raises(ValueError):
        subpath_to_manim_points([0, 0])
    with pytest.raises(ValueError):
        subpath_to_manim_points([0, 0, 1, 1, 2, 2])


def test_round_trip_is_exact():
    data = parse_points(SQUARE)
    pts = polymorph_data_to_manim_points(data)
    subpaths = [pts]  # single subpath
    assert manim_subpaths_to_polymorph_data(subpaths) == data


def test_multi_subpath_concatenation():
    data = parse_points("M0 0 L10 0 L10 10 Z M20 20 L30 20 L30 30 Z")
    assert len(data) == 2
    pts = polymorph_data_to_manim_points(data)
    per_subpath = [len(subpath_to_manim_points(ns)) for ns in data]
    assert pts.shape == (sum(per_subpath), 3)
    # discontinuity between the two subpaths marks the boundary for manim
    boundary = per_subpath[0]
    assert not np.array_equal(pts[boundary - 1], pts[boundary])


def test_closed_path_snapping():
    data = parse_points(SQUARE)
    pts = polymorph_data_to_manim_points(data)
    drifted = pts.copy()
    drifted[-1, :2] += 1e-9  # simulate float drift on the closing anchor
    flat = manim_subpaths_to_polymorph_data([drifted])[0]
    assert flat[-2] == flat[0] and flat[-1] == flat[1]

    open_pts = pts.copy()
    open_pts[-1, :2] += 0.5  # genuinely open: must not be snapped
    flat = manim_subpaths_to_polymorph_data([open_pts])[0]
    assert (flat[-2], flat[-1]) != (flat[0], flat[1])


def test_numeric_morph_endpoints_and_midpoint():
    left = parse_points(SQUARE)
    right = parse_points(CIRCLE)
    morph = NumericMorph([left, right])
    p0 = morph.points_at(0.0)
    p1 = morph.points_at(1.0)
    mid = morph.points_at(0.5)
    assert p0.shape == p1.shape == mid.shape  # identical structure at all t
    assert np.allclose(mid, (p0 + p1) / 2)


def test_numeric_morph_endpoint_structure_matches_interior():
    # the whole point of the numeric layer: no short-circuit pop at t=0/1
    morph = NumericMorph([parse_points(SQUARE), parse_points(CIRCLE)])
    assert np.allclose(morph.points_at(0.0), morph.points_at(1e-9), atol=1e-6)
    assert np.allclose(morph.points_at(1.0), morph.points_at(1 - 1e-9), atol=1e-6)


def test_numeric_morph_multi_keyframe_dispatch():
    a = parse_points(SQUARE)
    b = parse_points(CIRCLE)
    c = parse_points("M0 0 L20 0 L10 20 Z")
    morph = NumericMorph([a, b, c])
    assert morph.num_segments == 2
    assert morph.segment_of(0.0) == (0, 0.0)
    h, s = morph.segment_of(0.25)
    assert h == 0 and s == pytest.approx(0.5)
    h, s = morph.segment_of(0.5)
    assert (h, s) == (1, 0.0) or (h == 0 and s == pytest.approx(1.0))
    h, s = morph.segment_of(1.0)
    assert h == 1 and s == pytest.approx(1.0)  # clamped to last segment


def test_numeric_morph_overshoot_extrapolates():
    left = parse_points(SQUARE)
    right = parse_points(CIRCLE)
    morph = NumericMorph([left, right])
    p1 = morph.points_at(1.0)
    p11 = morph.points_at(1.1)
    p0 = morph.points_at(0.0)
    assert np.allclose(p11, p1 + (p1 - p0) * 0.1)


def test_numeric_morph_requires_two_keyframes():
    with pytest.raises(ValueError):
        NumericMorph([parse_points(SQUARE)])
