import pytest

from polymorph import js_round, make_formatter, render_path


def test_renders_a_segment_properly():
    start = [[0, 10, 20, 20, 40, 40, 50, 50]]
    assert render_path(start) == "M 0 10 C 20 20 40 40 50 50"


def test_passes_strings_through():
    assert render_path("M 0 0 L 1 1") == "M 0 0 L 1 1"


def test_suppresses_consecutive_duplicate_point_curves():
    start = [[0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]]
    assert render_path(start) == "M 0 0 C 5 5 5 5 5 5"


def test_keeps_non_consecutive_duplicate_points():
    start = [[0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 10, 10, 5, 5, 5, 5, 5, 5]]
    assert render_path(start) == "M 0 0 C 5 5 5 5 5 5 0 0 0 0 10 10"


def test_renders_multiple_subpaths():
    start = [[0, 0, 1, 1, 2, 2, 3, 3], [4, 4, 5, 5, 6, 6, 7, 7]]
    assert render_path(start) == "M 0 0 C 1 1 2 2 3 3 M 4 4 C 5 5 6 6 7 7"


def test_precision_formatter_produces_fixed_decimals():
    start = [[0.5, 10, 1.5, 2.25, 3.126, 4, 5, 6]]
    assert (
        render_path(start, make_formatter(2)) == "M 0.50 10.00 C 1.50 2.25 3.13 4.00 5.00 6.00"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.5, 1),
        (-0.5, 0),
        (2.5, 3),
        (-2.5, -2),
        (-0.6, -1),
        (2.4, 2),
        (-2.4, -2),
    ],
)
def test_js_round_matches_javascript_math_round(value, expected):
    assert js_round(value) == expected
