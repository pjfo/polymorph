"""Coverage for arc-to-bezier conversion (untested in polymorph-js)."""

import math

import pytest

from polymorph.arc import arc_to_curve


def curve_endpoints(beziers):
    return [(beziers[i + 4], beziers[i + 5]) for i in range(0, len(beziers), 6)]


def test_non_positive_radius_degrades_to_a_line():
    assert arc_to_curve(0, 0, 0, 10, 0, 0, 0, 50, 50) == [0, 0, 50, 50, 50, 50]
    assert arc_to_curve(0, 0, 10, -1, 0, 0, 0, 50, 50) == [0, 0, 50, 50, 50, 50]


def test_small_arc_is_a_single_curve_ending_at_the_endpoint():
    # quarter circle: 90 degrees <= 120, so one bezier
    beziers = arc_to_curve(50, 0, 50, 50, 0, 0, 1, 0, 50)
    assert len(beziers) == 6
    assert beziers[4] == pytest.approx(0, abs=1e-9)
    assert beziers[5] == pytest.approx(50, abs=1e-9)


def test_large_sweep_splits_into_multiple_curves():
    # half circle: 180 degrees > 120, split into two beziers
    beziers = arc_to_curve(0, 0, 50, 50, 0, 0, 0, 100, 0)
    assert len(beziers) == 12
    # every curve endpoint must lie on the circle centered at (50, 0)
    for x, y in curve_endpoints(beziers):
        assert math.hypot(x - 50, y - 0) == pytest.approx(50, abs=1e-9)
    assert curve_endpoints(beziers)[-1] == (pytest.approx(100), pytest.approx(0, abs=1e-9))


def test_large_arc_flag_takes_the_long_way_around():
    small = arc_to_curve(0, 0, 50, 50, 0, 0, 0, 50, 50)
    large = arc_to_curve(0, 0, 50, 50, 0, 1, 0, 50, 50)
    # the large arc sweeps 270 degrees and needs more curves than the 90 degree arc
    assert len(large) > len(small)
    assert curve_endpoints(large)[-1] == (pytest.approx(50), pytest.approx(50))


def test_sweep_flag_mirrors_the_arc():
    ccw = arc_to_curve(0, 0, 50, 50, 0, 0, 0, 100, 0)
    cw = arc_to_curve(0, 0, 50, 50, 0, 0, 1, 100, 0)
    # counter-clockwise bulges up (negative y in SVG terms differs from clockwise)
    ccw_mid_y = ccw[5]
    cw_mid_y = cw[5]
    assert ccw_mid_y == pytest.approx(-cw_mid_y, abs=1e-9)
    assert ccw_mid_y != cw_mid_y


def test_rotation_angle_rotates_the_curve():
    flat = arc_to_curve(0, 0, 40, 10, 0, 0, 1, 80, 0)
    rotated = arc_to_curve(0, 0, 40, 10, 45, 0, 1, 80, 0)
    assert flat != rotated
    # both still end at the requested endpoint
    assert curve_endpoints(rotated)[-1] == (pytest.approx(80), pytest.approx(0, abs=1e-9))


def test_radii_too_small_are_scaled_up():
    # radius 10 cannot span points 100 apart; the algorithm scales it to 50
    beziers = arc_to_curve(0, 0, 10, 10, 0, 0, 1, 100, 0)
    assert curve_endpoints(beziers)[-1] == (pytest.approx(100), pytest.approx(0, abs=1e-9))
    for x, y in curve_endpoints(beziers):
        assert math.hypot(x - 50, y) == pytest.approx(50, abs=1e-9)
