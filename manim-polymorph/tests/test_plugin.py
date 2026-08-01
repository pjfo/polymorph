"""Plugin registration and public API surface."""

from importlib.metadata import entry_points

import pytest

pytest.importorskip("manim")


def test_entry_point_registered():
    names = [ep.name for ep in entry_points(group="manim.plugins")]
    assert "manim_polymorph" in names


def test_public_api():
    import manim_polymorph

    for name in manim_polymorph.__all__:
        assert getattr(manim_polymorph, name) is not None
    assert manim_polymorph.__version__
