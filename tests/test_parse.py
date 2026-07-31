"""Golden vectors ported verbatim from polymorph-js tests/operators/parsePath.ts."""

import pytest

from polymorph import Path, js_round, parse_points, render_path


def rendered(d: str) -> str:
    return render_path(parse_points(d), js_round)


def test_parses_terms_properly_with_spaces():
    assert Path("M 10 42 v 0").get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_ignores_spaces_tabs_and_new_lines():
    assert Path("M10,42\n \tv0").get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_parses_terms_properly_with_commas():
    assert Path("M10,42v0").get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_parses_move():
    assert Path("M 10 42v0").get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_parses_close_path():
    assert Path("M 10 42z").get_data()[0] == [10, 42, 10, 42, 10, 42, 10, 42]


def test_parses_h_relative():
    assert Path("M 10 50 h 50").get_data()[0] == [10, 50, 10, 50, 10, 50, 60, 50]


def test_parses_h_absolute():
    assert Path("M 10 50 H 60").get_data()[0] == [10, 50, 10, 50, 10, 50, 60, 50]


def test_parses_v_relative():
    assert Path("M 50 10 v 50").get_data()[0] == [50, 10, 50, 10, 50, 10, 50, 60]


def test_parses_v_absolute():
    assert Path("M 50 10 V 60").get_data()[0] == [50, 10, 50, 10, 50, 10, 50, 60]


def test_parses_l_relative():
    assert Path("M 10 10 l 10 10").get_data()[0] == [10, 10, 10, 10, 10, 10, 20, 20]


def test_parses_l_absolute():
    assert Path("M 10 10 L 20 20").get_data()[0] == [10, 10, 10, 10, 10, 10, 20, 20]


def test_parses_c_relative():
    assert Path("M 10 10 c 10 5 5 10 25 25").get_data()[0] == [10, 10, 20, 15, 15, 20, 35, 35]


def test_parses_c_absolute():
    assert Path("M 10 10 C 20 15 15 20 35 35").get_data()[0] == [10, 10, 20, 15, 15, 20, 35, 35]


def test_parses_s_relative():
    assert Path("M 10 10 s 50 35 55 85").get_data()[0] == [10, 10, 10, 10, 60, 45, 65, 95]


def test_parses_s_plus_s():
    actual = Path("M 10 10 s 10 40 25 25 s 10 40 25 25").get_data()[0]
    assert actual == [10, 10, 10, 10, 20, 50, 35, 35, 50, 20, 45, 75, 60, 60]


def test_parses_s_with_multiple_argument_sets():
    assert (
        rendered("M 10 10 s 10 40 25 25 10 40 25 25")
        == "M 10 10 C 10 10 20 50 35 35 50 20 45 75 60 60"
    )


def test_parses_s_absolute():
    assert Path("M 10 10 S 20 15 35 35").get_data()[0] == [10, 10, 10, 10, 20, 15, 35, 35]


def test_parses_s_plus_s_absolute():
    actual = Path("M 10 10 S 20 50 35 35 S 45 75 60 60").get_data()[0]
    assert actual == [10, 10, 10, 10, 20, 50, 35, 35, 50, 20, 45, 75, 60, 60]


def test_parses_s_absolute_with_multiple_argument_sets():
    assert (
        rendered("M 10 10 S 20 50 35 35 45 75 60 60")
        == "M 10 10 C 10 10 20 50 35 35 50 20 45 75 60 60"
    )


def test_parses_c_followed_by_s():
    assert (
        rendered("M 10 10 c10 10 10 40 25 25 s10 40 25 25")
        == "M 10 10 C 20 20 20 50 35 35 50 20 45 75 60 60"
    )


def test_parses_q_relative():
    assert rendered("M 10 10 q 10 5 15 25") == "M 10 10 C 17 13 22 22 25 35"


def test_parses_q_absolute():
    assert rendered("M 10 10 Q 20 15 25 35") == "M 10 10 C 17 13 22 22 25 35"


def test_parses_t_relative():
    assert rendered("M 10 10 t 15 25") == "M 10 10 C 10 10 10 10 25 35"


def test_parses_t_plus_t():
    assert (
        rendered("M 10 10 t 15 25 t 25 15") == "M 10 10 C 10 10 10 10 25 35 35 52 43 57 50 50"
    )


def test_parses_t_with_multiple_argument_sets():
    assert rendered("M 10 10 t 15 25 25 15") == "M 10 10 C 10 10 10 10 25 35 35 52 43 57 50 50"


def test_parses_t_absolute():
    assert rendered("M 10 10 T 25 35") == "M 10 10 C 10 10 10 10 25 35"


def test_parses_t_plus_t_absolute():
    assert (
        rendered("M 10 10 T 25 35 T 70 50") == "M 10 10 C 10 10 10 10 25 35 35 52 50 57 70 50"
    )


def test_parses_t_absolute_with_multiple_argument_sets():
    assert rendered("M 10 10 T 25 35 70 50") == "M 10 10 C 10 10 10 10 25 35 35 52 50 57 70 50"


def test_parses_multi_segment_paths():
    actual = Path("M0,0 V12 H12 V0z M16,16 V20 H20 V16z")
    expected = [
        [0, 0, 0, 0, 0, 0, 0, 12, 0, 12, 0, 12, 12, 12, 12, 12, 12, 12, 12, 0, 12, 0, 12, 0, 0, 0],
        [
            16, 16, 16, 16, 16, 16, 16, 20, 16, 20, 16, 20, 20, 20, 20, 20, 20, 20, 20, 16, 20,
            16, 20, 16, 16, 16,
        ],
    ]
    assert actual.get_data() == expected


def test_parses_a_relative():
    assert (
        rendered("M25 25 a20 20 30 0 0 50 50")
        == "M 25 25 C 6 44 15 77 41 84 53 87 66 84 75 75"
    )


def test_parses_a_with_sweep_flag():
    assert (
        rendered("M25 25 a20 20 30 0 1 50 50")
        == "M 25 25 C 44 6 77 15 84 41 87 53 84 66 75 75"
    )


def test_parses_a_with_large_flag():
    assert (
        rendered("M0,0 a20 5 90 1 0 100 0")
        == "M 0 0 C 0 154 42 250 75 173 90 137 100 71 100 0"
    )


def test_parses_a_with_multiple_arcs():
    actual = rendered("M20,20 a10 10 45 1 0 0 25 10 10 45 1 0 0 25 10 10 45 1 0 0 25")
    assert actual == (
        "M 20 20 C 10 20 4 30 9 39 11 43 16 45 20 45 10 45 4 55 9 64 11 68 16 70 20 70"
        " 10 70 4 80 9 89 11 93 16 95 20 95"
    )


def test_parses_a_absolute():
    assert (
        rendered("M25 25 A20 20 30 0 0 50 50") == "M 25 25 C 20 40 34 54 49 50 49 50 50 50 50 50"
    )


def test_parses_a_absolute_with_sweep_flag():
    assert (
        rendered("M25 25 A20 20 30 0 1 50 50") == "M 25 25 C 40 20 54 34 50 49 50 49 50 50 50 50"
    )


def test_parses_a_absolute_with_large_flag():
    assert (
        rendered("M25 25 A20 5 90 1 0 50 50") == "M 25 25 C 23 63 32 98 41 87 45 82 49 68 50 50"
    )


# --- new error-handling coverage (the JS library silently produced NaNs) ---


def test_raises_when_path_does_not_start_with_move():
    with pytest.raises(ValueError, match="must start with a move"):
        parse_points("L 10 10")


def test_raises_on_unsupported_command():
    # F is not a recognized command letter, so it corrupts the adjacent number
    with pytest.raises(ValueError, match="invalid number"):
        parse_points("M 0 0 F 10 10")


def test_raises_on_leading_garbage():
    with pytest.raises(ValueError, match="not a supported"):
        parse_points("10 20 M 0 0")


def test_raises_on_insufficient_arguments():
    with pytest.raises(ValueError):
        parse_points("M 10")


def test_raises_on_empty_string():
    with pytest.raises(ValueError):
        parse_points("")
