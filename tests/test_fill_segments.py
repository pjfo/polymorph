"""Ported from polymorph-js tests/operators/fillSegments.ts."""

from polymorph import Origin, Path
from polymorph.normalize import fill_segments

TWO_SQUARES = "M0,0 V12 H12 V0z M16,16 V20 H20 V16z"
ONE_SQUARE = "M0,0 V12 H12 V0z"


def test_fills_segments_from_the_right():
    left = Path(TWO_SQUARES).get_data()
    right = Path(ONE_SQUARE).get_data()
    fill_segments(left, right, Origin(0, 0))
    assert len(left) == len(right)


def test_fills_segments_from_the_left():
    left = Path(ONE_SQUARE).get_data()
    right = Path(TWO_SQUARES).get_data()
    fill_segments(left, right, Origin(0, 0))
    assert len(left) == len(right)


def test_filled_segment_is_degenerate_at_the_origin():
    left = Path(TWO_SQUARES).get_data()
    right = Path(ONE_SQUARE).get_data()
    fill_segments(left, right, Origin(0, 0))
    added = right[1]
    # relative origin (0, 0) maps to the matched subpath's bbox top-left (16, 16)
    assert len(added) == len(left[1])
    assert added[0::2] == [16.0] * (len(added) // 2)
    assert added[1::2] == [16.0] * (len(added) // 2)
