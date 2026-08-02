"""The Polymorph animation: morph a VMobject through keyframe shapes."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from manim import Animation, VMobject
from polymorph.normalize import Origin

from .core import NumericMorph, manim_subpaths_to_polymorph_data
from .mobject import _ensure_cairo_cubics

__all__ = ["Polymorph", "PolymorphTransform"]


def _family_subpaths(vm: VMobject) -> list[np.ndarray]:
    """All subpaths in a VMobject's family, in draw order.

    Collecting per member (rather than concatenating raw points) keeps
    subpath boundaries exact even when one member's path happens to end
    where the next begins.
    """
    return [sp for m in vm.family_members_with_points() for sp in m.get_subpaths()]


def _style_donor(vm: VMobject) -> VMobject:
    """The family member whose style represents the whole mobject.

    For a plain shape this is the mobject itself; for Text/Tex it is the
    first glyph, since the parent carries no drawn style of its own.
    """
    members = vm.family_members_with_points()
    return members[0] if members else vm


class Polymorph(Animation):
    """Morph a VMobject through one or more target shapes using polymorph.

    Unlike Transform, subpaths are paired by sorted perimeter and closed
    subpaths rotate their start point toward a configurable origin —
    producing stable morphs between structurally different shapes. When
    subpath counts differ, the smaller keyframe's subpaths are shared out
    across the larger's by default (one shape splits into many, many
    merge into one, flubber-style); fill_mode="grow" restores polymorph's
    own behavior of growing the missing subpaths from the origin.

    Mobjects whose geometry lives in submobjects (Text, Tex, VGroup, SVG
    imports) are flattened: every subpath in the family joins one morph.
    While morphing, the animated mobject is collapsed to a single flat
    VMobject styled after its first drawn family member — per-glyph colors
    are not preserved mid-morph — and with snap_to_target the target's full
    submobject structure is restored on finish.

    mobject: the VMobject to animate (morphed in place).
    targets: one or more target VMobjects; with several, the run time is
        divided evenly between consecutive pairs, like polymorph's own
        multi-path interpolate. Targets do not need to be on screen.
    fill_mode: how subpath-count mismatches between keyframes are
        resolved. "share" (default) clones the smaller keyframe's
        subpaths so every subpath morphs from/to real geometry; "grow"
        pads with degenerate subpaths that grow from the origin.
    origin: where filler subpaths grow from (fill_mode="grow") and where
        closed subpaths start drawing. Relative origins use SVG semantics
        — (0, 0) is the top-left of each subpath's bounding box — while
        Origin(..., absolute=True) is a scene coordinate.
    add_points: extra curves added to every subpath (smooths morphs between
        shapes of very different complexity).
    optimize: "fill" (default) aligns subpaths automatically; "none"
        requires all keyframes to already share an identical structure.
    crossfade_style: interpolate fill/stroke style between the keyframes'
        styles while morphing.
    snap_to_target: on finish, adopt the final target's exact points and
        style instead of the normalized (padded/rotated) equivalent.
    """

    def __init__(
        self,
        mobject: VMobject,
        *targets: VMobject,
        fill_mode: Literal["share", "grow"] = "share",
        origin: tuple[float, float] | Origin = (0.0, 0.0),
        add_points: int = 0,
        optimize: Literal["fill", "none"] = "fill",
        crossfade_style: bool = True,
        snap_to_target: bool = True,
        **kwargs: Any,
    ) -> None:
        if not targets:
            raise ValueError("at least one target shape is required")
        for target in targets:
            if isinstance(target, str):
                raise TypeError(
                    "targets must be VMobjects, not d-strings; build them with "
                    "manim_polymorph.svg_path_mobjects so all keyframes share "
                    "one coordinate mapping"
                )
            if not isinstance(target, VMobject):
                raise TypeError(f"targets must be VMobjects, got {type(target).__name__}")
        if not isinstance(mobject, VMobject):
            raise TypeError(f"mobject must be a VMobject, got {type(mobject).__name__}")
        if not isinstance(origin, Origin):
            origin = Origin(*origin)

        self.targets = targets
        self.fill_mode = fill_mode
        self.origin = origin
        self.add_points = add_points
        self.optimize = optimize
        self.crossfade_style = crossfade_style
        self.snap_to_target = snap_to_target
        self._morph: NumericMorph | None = None
        self._keyframes: list[VMobject] = []
        self._donors: list[VMobject] = []
        super().__init__(mobject, **kwargs)

    def begin(self) -> None:
        _ensure_cairo_cubics()
        self._keyframes = [self.mobject.copy()] + [t.copy() for t in self.targets]
        datas = [
            manim_subpaths_to_polymorph_data(_family_subpaths(vm)) for vm in self._keyframes
        ]
        for vm, data in zip(self._keyframes, datas):
            if not data:
                raise ValueError(f"keyframe {vm} has no points to morph")
        self._donors = [_style_donor(vm) for vm in self._keyframes]
        if self.mobject.submobjects:
            # collapse the family onto the parent for the duration of the
            # morph; interpolate_mobject supplies the flattened points
            self.mobject.submobjects = []
            self.mobject.match_style(self._donors[0])
        origin = self.origin
        if not origin.absolute:
            # relative origins keep the SVG mental model, where (0, 0) is the
            # top-left; scene y grows upward, so flip the y fraction
            origin = Origin(origin.x, 1.0 - origin.y)
        self._morph = NumericMorph(
            datas,
            optimize=self.optimize,
            origin=origin,
            add_points=self.add_points,
            fill_mode=self.fill_mode,
        )
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        # alpha arrives raw here; unlike interpolate_submobject overrides,
        # the rate function must be applied manually
        t = self.rate_func(alpha)
        self.mobject.set_points(self._morph.points_at(t))
        if self.crossfade_style:
            h, s = self._morph.segment_of(t)
            self.mobject.interpolate_color(
                self._donors[h], self._donors[h + 1], min(max(s, 0.0), 1.0)
            )

    def finish(self) -> None:
        super().finish()
        if self.snap_to_target:
            final = self._keyframes[-1]
            self.mobject.set_points(final.points.copy())
            self.mobject.match_style(final)
            # hand over the keyframe copy's family so structured targets
            # (Text, Tex, groups) come out with their glyphs intact
            self.mobject.submobjects = list(final.submobjects)


PolymorphTransform = Polymorph
