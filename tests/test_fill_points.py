"""Ported from polymorph-js tests/operators/fillPoints.ts."""

from polymorph.normalize import fill_points, fill_subpath

START = [10, 10, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]


def test_returns_the_same_path_if_the_same_length_is_set():
    actual = fill_subpath(list(START), 20)
    assert len(actual) == 20
    assert actual == START


def test_fills_the_path_when_a_new_set_is_available():
    actual = fill_subpath(list(START), 26)
    assert len(actual) == 26
    assert actual == [
        10, 10,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 1,
        2, 2, 2, 2, 2, 2,
    ]


def test_fills_the_path_evenly_if_there_are_twice_as_many_elements():
    actual = fill_subpath(list(START), 38)
    assert len(actual) == 38
    assert actual == [
        10, 10,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1,
        2, 2, 2, 2, 2, 2,
    ]


def test_fill_points_equalizes_both_sides():
    left = [0, 0, 1, 1, 1, 1, 1, 1]
    right = [0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]
    matrix = [[left], [right]]
    fill_points(matrix, 0)
    assert len(matrix[0][0]) == len(matrix[1][0]) == 14


def test_fill_subpath_handles_more_padding_than_the_per_curve_ratio():
    # polymorph-js produced NaNs when the target length exceeded roughly
    # double the source length; the port pads at the final endpoint instead
    actual = fill_subpath([0, 0, 1, 1, 1, 1, 1, 1], 32)
    assert len(actual) == 32
    assert actual == [0, 0, 1, 1, 1, 1, 1, 1] + [1, 1, 1, 1, 1, 1] * 4
