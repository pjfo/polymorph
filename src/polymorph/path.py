"""The Path class: a parsed SVG path that can be rendered or morphed."""

from __future__ import annotations

from collections.abc import Sequence

from .parse import parse_points
from .render import Formatter, render_path


class Path:
    """A parsed SVG path.

    Accepts SVG path data (a d-string), another Path, or pre-parsed
    poly-bezier data (a sequence of flat subpath coordinate sequences).
    """

    def __init__(self, source: str | Path | Sequence[Sequence[float]]) -> None:
        self._string_data: str | None
        if isinstance(source, Path):
            self._data = [list(segment) for segment in source._data]
            self._string_data = source._string_data
        elif isinstance(source, str):
            self._data = parse_points(source)
            self._string_data = source
        else:
            self._data = [[float(value) for value in segment] for segment in source]
            self._string_data = None

    def get_data(self) -> list[list[float]]:
        """The poly-bezier data: one flat coordinate list per subpath."""
        return self._data

    def get_string_data(self) -> str:
        """The original d-string if one was supplied, else a rendered one (cached)."""
        if self._string_data is None:
            self._string_data = self.render()
        return self._string_data

    def render(self, formatter: Formatter | None = None) -> str:
        """Render this path as an SVG path string."""
        return render_path(self._data, formatter)

    def __repr__(self) -> str:
        return f"Path({self.get_string_data()!r})"
