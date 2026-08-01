from contextlib import contextmanager

import pytest


@pytest.fixture
def opengl_renderer():
    """Temporarily switch manim to the OpenGL renderer.

    manim's own tempconfig cannot be used here: it restores config through a
    raw _d.update that bypasses the renderer property setter, leaving every
    ConvertToOpenGL class with its bases still swapped to the OpenGL variants.
    Assigning through the property both ways keeps the bases consistent.
    """
    from manim import config

    @contextmanager
    def _switch():
        old = config.renderer
        config.renderer = "opengl"
        try:
            yield
        finally:
            config.renderer = old

    return _switch
