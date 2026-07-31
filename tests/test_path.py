"""Coverage for the Path class (untested in polymorph-js)."""

from polymorph import Path, interpolate, make_formatter

SQUARE = "M0,0 H10 V10 H0 Z"


def test_constructs_from_path_data_string():
    path = Path("M 10 42 v 0")
    assert path.get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_constructs_from_point_data():
    data = [[0, 10, 20, 20, 40, 40, 50, 50]]
    path = Path(data)
    assert path.get_data() == [[0.0, 10.0, 20.0, 20.0, 40.0, 40.0, 50.0, 50.0]]
    # the input is copied, not shared
    data[0][0] = 999
    assert path.get_data()[0][0] == 0.0


def test_constructs_from_another_path():
    original = Path(SQUARE)
    copy = Path(original)
    assert copy.get_data() == original.get_data()
    assert copy.get_data() is not original.get_data()
    assert copy.get_string_data() == SQUARE


def test_get_string_data_returns_the_original_string():
    path = Path(SQUARE)
    assert path.get_string_data() == SQUARE


def test_get_string_data_renders_and_caches_for_point_data():
    path = Path([[0, 10, 20, 20, 40, 40, 50, 50]])
    rendered = path.get_string_data()
    assert rendered == "M 0 10 C 20 20 40 40 50 50"
    assert path.get_string_data() is rendered


def test_render_accepts_a_custom_formatter():
    path = Path([[0.5, 10, 1.5, 2.25, 3.126, 4, 5, 6]])
    assert path.render(make_formatter(2)) == "M 0.50 10.00 C 1.50 2.25 3.13 4.00 5.00 6.00"


def test_paths_are_reusable_across_interpolations():
    # polymorph-js mutated Path data during normalization; the port must not
    left = Path(SQUARE)
    right = Path("M5,5 H40 V40 H5 Z M50,50 h2 v2 h-2 z")
    before_left = [list(s) for s in left.get_data()]
    before_right = [list(s) for s in right.get_data()]

    first = interpolate([left, right])(0.5)
    second = interpolate([left, right])(0.5)

    assert left.get_data() == before_left
    assert right.get_data() == before_right
    assert first == second
