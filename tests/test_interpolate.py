"""mix_points cases ported from polymorph-js tests/operators/interpolatePath.ts,
plus new coverage for interpolate() itself."""

import pytest

from polymorph import Path, interpolate, mix_points

SQUARE_A = "M0,0 H10 V10 H0 Z"
SQUARE_B = "M0,0 H20 V20 H0 Z"
SQUARE_C = "M0,0 H40 V40 H0 Z"


def test_finds_the_midpoint_when_25_is_provided():
    assert mix_points([0, 0, 0], [10, 100, 1000], 0.25) == [2.5, 25, 250]


def test_finds_the_midpoint_when_5_is_provided():
    assert mix_points([0, 0, 0], [10, 100, 1000], 0.5) == [5, 50, 500]


def test_finds_the_midpoint_when_75_is_provided():
    assert mix_points([0, 0, 0], [10, 100, 1000], 0.75) == [7.5, 75, 750]


def test_requires_at_least_two_paths():
    with pytest.raises(ValueError, match="at least two"):
        interpolate([SQUARE_A])


def test_rejects_unknown_optimize_value():
    with pytest.raises(ValueError, match="optimize"):
        interpolate([SQUARE_A, SQUARE_B], optimize="magic")


def test_rejects_negative_add_points_and_precision():
    with pytest.raises(ValueError):
        interpolate([SQUARE_A, SQUARE_B], add_points=-1)
    with pytest.raises(ValueError):
        interpolate([SQUARE_A, SQUARE_B], precision=-1)


def test_offset_0_and_1_return_the_original_strings():
    f = interpolate([SQUARE_A, SQUARE_B])
    assert f(0) == SQUARE_A
    assert f(1) == SQUARE_B


def test_midpoint_is_valid_path_data():
    f = interpolate([SQUARE_A, SQUARE_B])
    d = f(0.5)
    assert d.startswith("M ")
    assert " C " in d
    # midpoint of a 10x10 and a 20x20 square is a 15x15 square
    assert "15 15" in d


def test_three_paths_use_the_correct_local_offset():
    # polymorph-js had a bug where segments after the first used a scaled-down
    # local offset; global 0.75 across [a, b, c] must equal pair [b, c] at 0.5
    combined = interpolate([SQUARE_A, SQUARE_B, SQUARE_C])
    pair = interpolate([SQUARE_B, SQUARE_C])
    assert combined(0.75) == pair(0.5)


def test_three_paths_hit_the_middle_path_exactly():
    combined = interpolate([SQUARE_A, SQUARE_B, SQUARE_C])
    assert combined(0.5) == SQUARE_B


def test_accepts_path_objects_and_point_data():
    f = interpolate([Path(SQUARE_A), Path(SQUARE_B).get_data()])
    assert f(0.5).startswith("M ")


def test_precision_controls_decimal_places():
    f = interpolate([SQUARE_A, SQUARE_B], precision=2)
    d = f(0.25)
    assert "12.50" in d


def test_offsets_outside_range_extrapolate():
    f = interpolate([SQUARE_A, SQUARE_B])
    assert f(1.5).startswith("M ")
    assert f(-0.5).startswith("M ")


def test_optimize_none_with_matching_structure():
    f = interpolate([SQUARE_A, SQUARE_B], optimize="none")
    assert f(0.5).startswith("M ")


def test_optimize_none_with_mismatched_structure_raises():
    with pytest.raises(ValueError):
        interpolate([SQUARE_A, SQUARE_A + " M20,20 h2 v2 h-2 z"], optimize="none")
