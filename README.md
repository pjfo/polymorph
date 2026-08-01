# Polymorph

*Morph SVG paths in pure Python*

A Python port of [polymorph-js](https://github.com/notoriousb1t/polymorph) by Christopher Wallis.

## Features

- morphs between two or more SVG paths with a single function
- handles paths with different numbers of subpaths and holes in paths
- pure Python, zero dependencies
- supports all SVG path commands (M, L, H, V, C, S, Q, T, A, Z — absolute and relative)
- free for commercial and non-commercial use under the MIT license

## Demo

An interactive demo (chain morph, subpath morph, live path data) lives at
[pjfo.github.io/polymorph](https://pjfo.github.io/polymorph/). It is generated
straight from this library by `demo/generate.py` and deployed by GitHub
Actions on every push to `master`.

## Examples

[`examples/star_morph.py`](examples/star_morph.py) drives a
[Manim](https://www.manim.community/) animation with polymorph: a small
five-pointed star nested in the troughs of a larger one morphs outward to
fill it. The rendered video (and the code that produced it) is on the
[demo page](https://pjfo.github.io/polymorph/).

## Install

```bash
pip install polymorph-py
```

## Quick start

```python
from polymorph import interpolate

f = interpolate([
    "M0,0 H20 V20 H0 Z",                # a square
    "M10,0 A10,10 0 1,1 9.99,0 Z",      # a circle
])

f(0)     # 'M0,0 H20 V20 H0 Z'  (the original input)
f(0.5)   # 'M 5 0 C 5 0 5 0 15 0 19 0 21 4 19 18 ...'  (halfway between)
f(1)     # 'M10,0 A10,10 0 1,1 9.99,0 Z'
```

Feed the returned function offsets between 0 and 1 (from any animation or
easing source) and set the result as the `d` attribute of an SVG `<path>`.

## API

### `interpolate(paths, *, add_points=0, optimize="fill", origin=(0, 0), precision=0)`

Returns a function `(offset: float) -> str` that produces SVG path data.

- **paths**: a sequence of two or more paths. Each may be a `d`-string, a
  `Path` object, or pre-parsed poly-bezier data. With more than two paths,
  the offset range is divided evenly between consecutive pairs (three paths:
  0 → 0.5 morphs the first pair, 0.5 → 1 the second).
- **add_points**: extra curve points added to every subpath. Increase this
  when morphing between paths of very different complexity to get smoother
  motion.
- **optimize**: `"fill"` (default) automatically matches up subpaths — sorts
  them by size, pads missing subpaths, and aligns starting points. `"none"`
  skips all of that and requires both paths to already have identical
  structure.
- **origin**: an `(x, y)` tuple or `Origin(x, y, absolute=False)`. Controls
  where padded subpaths grow from and where closed subpaths start drawing.
  By default coordinates are fractions of each subpath's bounding box
  (`(0, 0)` = top-left); pass `Origin(x, y, absolute=True)` for absolute
  SVG coordinates.
- **precision**: decimal places in the output. `0` (recommended) rounds to
  whole numbers.

At offsets 0 and 1 the original input strings are returned verbatim.

### `Path(source)`

A parsed SVG path. Accepts a `d`-string, another `Path`, or a list of flat
subpath coordinate lists.

```python
from polymorph import Path

path = Path("M0,0 H10 V10 H0 Z")
path.get_data()         # [[0.0, 0.0, 0.0, 0.0, ...]]  poly-bezier data
path.get_string_data()  # the original d-string
path.render()           # re-rendered as 'M ... C ...'
```

`Path` objects are immutable from `interpolate`'s point of view and can be
reused across many interpolators.

### Lower-level pieces

`parse_points(d)`, `render_path(data, formatter)`, `mix_points(a, b, offset)`,
`make_formatter(precision)`, and `js_round(n)` are exported for advanced use.

## How it works

Every path command is converted to absolute cubic bezier curves at parse
time, so a path becomes a list of flat coordinate arrays (one per subpath).
To morph, both paths are normalized to the same structure — subpaths sorted
largest-first, missing subpaths padded with degenerate points at the origin,
closed subpaths rotated to start from the same corner, and point counts
equalized — after which morphing is a simple linear interpolation of the
coordinates.

## Differences from polymorph-js

This port is behavior-compatible with polymorph-js with these deliberate
exceptions:

- **Bug fixes**
  - With three or more paths, segments after the first now interpolate at
    the correct rate (the JS version scaled the local offset down).
  - Subpath start-point alignment measures the true distance to the origin
    (the JS version compared against the origin's x twice).
  - `Path` data is never mutated during interpolation, so paths and parsed
    data are safe to reuse.
  - Very large `add_points` values pad cleanly instead of producing NaNs.
- **Errors instead of NaN**: malformed path data, unsupported commands, and
  mismatched structure with `optimize="none"` raise `ValueError` instead of
  silently emitting `NaN` in the output.
- **float64**: math is done in Python floats (the JS version used
  `Float32Array`), so low-order digits can differ from JS output when
  `precision > 0`.
- **No DOM**: CSS selectors and `SVGPathElement` inputs are not supported —
  pass path data directly.
- As in the JS parser, scientific notation (`1e-5`) is not supported, and
  extra coordinate pairs after `M`/`m` start new subpaths rather than being
  implicit line-tos (the SVG spec says line-to).

## License

MIT — original library copyright Christopher Wallis.

## Special thanks

Special thanks to [@shshaw](https://twitter.com/shshaw) for the amazing logo
and artwork for the original library, and to Christopher Wallis
([@notoriousb1t](https://github.com/notoriousb1t)) for polymorph-js.
