"""Coverage for perimeter, bbox, rotation, and path normalization.

The perimeter case is ported from polymorph-js tests/operators/perimeterPoints.ts;
the rest is new coverage (untested in the original library).
"""

import pytest

from polymorph import Origin, parse_points
from polymorph.normalize import (
    compute_absolute_origin,
    compute_dimensions,
    normalize_paths,
    normalize_points,
    perimeter_points,
    rotate_points,
    sorted_segments,
)

SQUARE = "M0,0 H10 V10 H0 Z"


def test_sums_up_the_perimeter_when_going_clockwise():
    points = parse_points("M0,0 H20V20H0z")
    assert perimeter_points(points[0]) == 80


def test_rotate_points_rotates_left_in_place():
    ns = [1, 2, 3, 4, 5, 6]
    rotate_points(ns, 2)
    assert ns == [3, 4, 5, 6, 1, 2]


def test_compute_dimensions_uses_endpoints():
    points = parse_points(SQUARE)[0]
    assert compute_dimensions(points) == (0, 0, 10, 10)


def test_compute_absolute_origin_maps_relative_coordinates():
    points = parse_points(SQUARE)[0]
    assert compute_absolute_origin(0.5, 0.5, points) == (5, 5)
    assert compute_absolute_origin(0, 0, points) == (0, 0)
    assert compute_absolute_origin(1, 1, points) == (10, 10)


def test_sorted_segments_puts_largest_perimeter_first():
    segments = parse_points("M0,0 H2 V2 H0 Z M10,10 H30 V30 H10 Z")
    ordered = sorted_segments(segments)
    assert perimeter_points(ordered[0]) > perimeter_points(ordered[1])


def test_normalize_points_skips_open_subpaths():
    points = parse_points("M0,0 H10 V10")[0]
    before = list(points)
    normalize_points(False, 0, 0, points)
    assert points == before


def test_normalize_points_rotates_to_start_nearest_origin():
    # this distinguishes the fixed distance(x, y) call from the JS bug
    # distance(originX, originX, ...): with origin (0, 10) the nearest curve
    # starts at (0, 10); the buggy version would pick the curve at (0, 0)
    points = parse_points(SQUARE)[0]
    normalize_points(True, 0, 10, points)
    assert points[0:2] == [0, 10]
    assert points == [
        0, 10,
        0, 10, 0, 10, 0, 0,
        0, 0, 0, 0, 10, 0,
        10, 0, 10, 0, 10, 10,
        10, 10, 10, 10, 0, 10,
    ]


def test_normalize_points_keeps_shape_closed():
    points = parse_points(SQUARE)[0]
    normalize_points(False, 0.5, 1.0, points)
    assert points[0:2] == points[-2:]


def test_normalize_paths_copies_inputs():
    left = parse_points(SQUARE)
    right = parse_points("M0,0 H20 V20 H0 Z")
    left_before = [list(s) for s in left]
    right_before = [list(s) for s in right]
    normalize_paths(left, right, optimize="fill", origin=Origin(0, 0), add_points=0)
    assert left == left_before
    assert right == right_before


def test_normalize_paths_equalizes_structure():
    left = parse_points("M0,0 H10 V10 H0 Z M20,20 h2 v2 h-2 z")
    right = parse_points(SQUARE)
    matrix = normalize_paths(left, right, optimize="fill", origin=Origin(0, 0), add_points=0)
    assert len(matrix[0]) == len(matrix[1])
    for a, b in zip(matrix[0], matrix[1]):
        assert len(a) == len(b)


def test_normalize_paths_optimize_none_requires_equal_subpath_counts():
    left = parse_points("M0,0 H10 V10 H0 Z M20,20 h2 v2 h-2 z")
    right = parse_points(SQUARE)
    with pytest.raises(ValueError, match="equal subpath counts"):
        normalize_paths(left, right, optimize="none", origin=Origin(0, 0), add_points=0)


def test_normalize_paths_optimize_none_requires_equal_point_counts():
    left = parse_points("M0,0 H10 V10 H0 Z")
    right = parse_points("M0,0 H10 V10")
    with pytest.raises(ValueError, match="equal point counts"):
        normalize_paths(left, right, optimize="none", origin=Origin(0, 0), add_points=0)
