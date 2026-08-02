# manim-polymorph

[Polymorph](https://github.com/pjfo/polymorph) SVG path morphing as a
[ManimCE](https://www.manim.community/) plugin: morph a shape through any
number of SVG paths with polymorph's subpath alignment instead of Manim's
built-in `Transform` machinery.

Why not just `Transform`? Manim's `VMobject.align_points` pairs subpaths
strictly by document order and pads missing subpaths with degenerate curves
collapsed onto a single point. Polymorph instead sorts subpaths by perimeter
before pairing them and rotates each closed subpath's start point toward a
configurable origin — which makes morphs between structurally different
shapes (different subpath counts, holes, wildly different point counts) look
intentional rather than glitchy. When subpath counts differ, the smaller
keyframe's subpaths are shared out across the larger's by default — one
shape splits into every glyph of a word, and every glyph merges back into
one shape — with polymorph's grow-from-origin filler available as
`fill_mode="grow"`.

## Install

`manim-polymorph` depends on `manim>=0.19` and `polymorph-py>=2.0.0`. From a
clone of this repository:

```bash
pip install -e .                    # polymorph-py, from the repository root
pip install -e ./manim-polymorph    # the plugin
```

Installing the root package first satisfies the `polymorph-py` requirement
locally (it is not published to PyPI). With [uv](https://docs.astral.sh/uv/)
the `[tool.uv.sources]` entry in `manim-polymorph/pyproject.toml` resolves the
path dependency automatically.

The plugin registers a `manim.plugins` entry point, so it shows up in
`manim plugins -l`, and can be listed in `manim.cfg`:

```ini
[CLI]
plugins = manim_polymorph
```

Either way, import what you use explicitly — Manim does not star-import
plugin namespaces.

## Quickstart

```python
from manim import RED, WHITE, YELLOW, BLUE, Scene, smooth
from manim_polymorph import Polymorph, svg_path_mobjects

HEART = "M50 88 Q10 55 4 36 A23 23 0 0 1 50 24 A23 23 0 0 1 96 36 Q90 55 50 88 Z"
STAR = "M50 6 L61 38 L95 38 L67 58 L78 92 L50 71 L22 92 L33 58 L5 38 L39 38 Z"


class Demo(Scene):
    def construct(self):
        heart, star = svg_path_mobjects(
            [HEART, STAR], height=4,
            styles=[dict(fill_color=RED), dict(fill_color=YELLOW)],
        )
        shape = heart.copy()
        self.add(shape)
        self.play(Polymorph(shape, star, run_time=2, rate_func=smooth))
```

A fuller scene — multi-keyframe sequencing, a shape with a hole, origin
control — is in [`examples/demo.py`](examples/demo.py):

```bash
manim -pql manim-polymorph/examples/demo.py PolymorphDemo
```

## API

### `Polymorph(mobject, *targets, ...)`

An `Animation` that morphs `mobject` in place through one or more target
`VMobject`s. With several targets the run time divides evenly between
consecutive pairs, like polymorph's own multi-path `interpolate`. Targets do
not need to be added to the scene, and are never mutated. `PolymorphTransform`
is an alias.

Mobjects whose geometry lives in submobjects — `Text`, `Tex`, `VGroup`s, SVG
imports — are flattened: every subpath in the family joins one morph, so a
word morphs glyph subpaths and all. While morphing, the animated mobject is
collapsed to a single flat `VMobject` styled after its first drawn family
member; with `snap_to_target` a structured target's submobjects are restored
on finish.

Keyword options, besides the usual `Animation` ones (`run_time`, `rate_func`,
...):

- `fill_mode="share"` — how subpath-count mismatches are resolved. `"share"`
  clones the smaller keyframe's subpaths so every subpath morphs from/to real
  geometry (flubber-style split/merge); `"grow"` pads with degenerate
  subpaths that grow from the origin (polymorph's own behavior).
- `origin=(0, 0)` — where filler subpaths grow from (`fill_mode="grow"`) and
  where closed subpaths start drawing. Relative origins use SVG semantics
  ((0, 0) is the top-left of each subpath's bounding box; (0.5, 0.5) is the
  center); `Origin(x, y, absolute=True)` is a scene coordinate.
- `add_points=0` — extra curves added to every subpath; raise it to smooth
  morphs between shapes of very different complexity.
- `optimize="fill"` — `"fill"` aligns structurally different paths;
  `"none"` requires every keyframe to already share an identical structure.
- `crossfade_style=True` — interpolate fill/stroke style between the
  keyframes' styles while morphing.
- `snap_to_target=True` — end on the final target's exact points and style
  rather than the normalized (padded, rotated) equivalent.

The morph runs entirely on numpy point arrays: keyframe alignment happens once
when the animation begins, and each frame is a single vectorized lerp written
into the mobject with `set_points`. No SVG strings are rendered or parsed per
frame, and polymorph's t = 0/1 string short-circuit and integer coordinate
rounding never come into play.

### `svg_path_mobjects(ds, *, height=2.0, center=True, styles=None, **common_style)`

Build one styled `VMobject` per d-string under a **single shared coordinate
mapping**: one affine transform (uniform scale, y-flip, translation) computed
from the union bounding box of all paths, sized so the union fits `height`
scene units. Shapes keep their relative sizes and positions, so a morph
between them cannot jump or rescale mid-animation. This is the intended way to
prepare `Polymorph` keyframes from SVG data. Per-shape style dicts in `styles`
are merged over the common style kwargs.

### `svg_path_mobject(d, ...)` / `SVGPathVMobject`

A single `VMobject` from one d-string: parsed with polymorph (arcs and
quadratics included), flipped to Manim's y-up convention, then scaled to
`height` (or `width`) and centered. With `height=None, width=None` the shape
keeps raw SVG user units.

## Limitations

- **Cairo renderer only.** The OpenGL renderer's 3-point quadratic curves are
  not supported; a clear `NotImplementedError` is raised.
- 2D paths only (z is always 0), matching SVG.
- Submobject hierarchies are flattened for the morph, so per-submobject
  styling (e.g. `Text` with per-glyph colors) collapses to the first drawn
  member's style until the animation finishes.
- Style crossfading rides Manim's `interpolate_color`; gradients with a
  different number of colors per keyframe are not aligned (single colors and
  equal-length gradients work).

## Development

```bash
pip install -e .                          # repository root
pip install -e "./manim-polymorph[dev]"
python -m pytest manim-polymorph/tests -q
ruff check manim-polymorph
```

The core numeric layer (`manim_polymorph.core`) has no manim dependency and
its tests run without manim installed; the remaining test modules skip
themselves when manim is missing.
