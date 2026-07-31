"""End-to-end morphing scenarios."""

import re

from polymorph import Origin, interpolate

SQUARE = "M0,0 H20 V20 H0 Z"
CIRCLE = "M10,0 A10,10 0 1,1 9.99,0 Z"
TWO_SHAPES = "M0,0 H20 V20 H0 Z M30,30 h5 v5 h-5 z"

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
FINITE = re.compile(r"^[MC0-9.\- ]+$")


def assert_valid_path(d: str) -> None:
    assert d.startswith("M ")
    assert " C " in d
    assert FINITE.match(d), f"non-finite or unexpected token in {d!r}"
    coords = NUMBER.findall(d)
    # every C block carries the M point plus 6-tuples
    assert len(coords) >= 8


def test_square_to_circle_morph():
    f = interpolate([SQUARE, CIRCLE])
    assert f(0) == SQUARE
    assert f(1) == CIRCLE
    for offset in (0.25, 0.5, 0.75):
        assert_valid_path(f(offset))


def test_single_to_multi_subpath_morph():
    f = interpolate([SQUARE, TWO_SHAPES])
    d = f(0.5)
    assert d.count("M ") == 2
    assert_valid_path(d)


def test_precision_two_produces_decimal_output():
    f = interpolate([SQUARE, CIRCLE], precision=2)
    d = f(0.5)
    assert re.search(r"\d+\.\d\d ", d)
    assert_valid_path(d.replace(".", ""))


def test_absolute_origin_and_add_points():
    f = interpolate(
        [SQUARE, TWO_SHAPES], origin=Origin(0, 0, absolute=True), add_points=2
    )
    assert_valid_path(f(0.5))


def test_morph_is_monotonic_between_two_squares():
    f = interpolate(["M0,0 H10 V10 H0 Z", "M0,0 H30 V30 H0 Z"])
    sizes = []
    for offset in (0.25, 0.5, 0.75):
        coords = [float(v) for v in NUMBER.findall(f(offset))]
        sizes.append(max(coords))
    assert sizes == sorted(sizes)
    assert sizes[1] == 20
