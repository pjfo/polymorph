"""Generate demo/index.html.

Runs the polymorph library to normalize each pair of demo shapes, then bakes
the aligned coordinate matrices into a self-contained HTML page. The browser
only performs the same elementwise linear mix that interpolate()'s returned
closure performs — all parsing and normalization is done here, in Python.

Regenerate with:  python demo/generate.py
"""

from __future__ import annotations

import html
import json
import math
import sys
from pathlib import Path as FilePath

sys.path.insert(0, str(FilePath(__file__).resolve().parent.parent / "src"))

from polymorph import Origin, parse_points  # noqa: E402
from polymorph.normalize import normalize_paths  # noqa: E402


def star(cx=50.0, cy=54.0, outer=38.0, inner=15.5, points=5) -> str:
    vertices = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / points
        vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in vertices) + " Z"


SQUARE = "M18,18 H82 V82 H18 Z"
CIRCLE = "M50,12 A38,38 0 1,1 49.99,12 Z"
STAR = star()
HEART = (
    "M50,86 C28,68 12,50 12,32 C12,20 21,13 31,15 C39,17 46,24 50,32"
    " C54,24 61,17 69,15 C79,13 88,20 88,32 C88,50 72,68 50,86 Z"
)

ONE_BLOCK = "M20,20 H80 V80 H20 Z"
THREE_BLOCKS = "M14,38 h20 v24 h-20 Z M40,30 h20 v40 h-20 Z M66,38 h20 v24 h-20 Z"

CHAIN = [("square", SQUARE), ("circle", CIRCLE), ("star", STAR), ("heart", HEART)]


def matrix_for(left: str, right: str) -> list[list[list[float]]]:
    matrix = normalize_paths(
        parse_points(left), parse_points(right), optimize="fill", origin=Origin(0, 0), add_points=0
    )
    return [[[round(v, 2) for v in seg] for seg in side] for side in matrix]


def build_data() -> str:
    data = {
        "chain": {
            "names": [name for name, _ in CHAIN],
            "pairs": [
                matrix_for(CHAIN[i][1], CHAIN[i + 1][1]) for i in range(len(CHAIN) - 1)
            ],
        },
        "subpaths": matrix_for(ONE_BLOCK, THREE_BLOCKS),
    }
    return json.dumps(data, separators=(",", ":"))


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>polymorph — SVG path morphing in pure Python</title>
<style>
  :root {
    --bg: #F5F7F8;
    --surface: #FFFFFF;
    --ink: #1A2025;
    --muted: #5B6B74;
    --accent: #0FA3B1;
    --accent-strong: #0B7E8A;
    --accent-soft: rgba(15, 163, 177, 0.14);
    --line: #DDE4E8;
    --code-bg: #EDF1F3;
    --mono: ui-monospace, "SF Mono", "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace;
    --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0E1418;
      --surface: #162026;
      --ink: #E8EEF1;
      --muted: #8FA1AB;
      --accent: #2BC3D2;
      --accent-strong: #6FD9E4;
      --accent-soft: rgba(43, 195, 210, 0.16);
      --line: #24313A;
      --code-bg: #101A20;
    }
  }
  :root[data-theme="light"] {
    --bg: #F5F7F8; --surface: #FFFFFF; --ink: #1A2025; --muted: #5B6B74;
    --accent: #0FA3B1; --accent-strong: #0B7E8A; --accent-soft: rgba(15, 163, 177, 0.14);
    --line: #DDE4E8; --code-bg: #EDF1F3;
  }
  :root[data-theme="dark"] {
    --bg: #0E1418; --surface: #162026; --ink: #E8EEF1; --muted: #8FA1AB;
    --accent: #2BC3D2; --accent-strong: #6FD9E4; --accent-soft: rgba(43, 195, 210, 0.16);
    --line: #24313A; --code-bg: #101A20;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
    line-height: 1.55;
  }
  main { max-width: 880px; margin: 0 auto; padding: 40px 20px 64px; }

  header { display: flex; flex-direction: column; gap: 6px; margin-bottom: 32px; }
  .eyebrow {
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent-strong);
  }
  h1 {
    margin: 0;
    font-family: var(--mono);
    font-size: clamp(28px, 5vw, 40px);
    font-weight: 600;
    letter-spacing: -0.02em;
    text-wrap: balance;
  }
  .tagline { margin: 0; color: var(--muted); max-width: 60ch; }

  .stage-card, .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
  }
  .stage-card { padding: 28px 28px 24px; display: flex; flex-direction: column; gap: 18px; }
  .stage { display: flex; justify-content: center; }
  .stage svg { width: min(360px, 78vw); height: auto; }
  .shape {
    fill: var(--accent-soft);
    stroke: var(--accent);
    stroke-width: 1.6;
    stroke-linejoin: round;
  }

  .chain-labels {
    display: flex;
    justify-content: space-between;
    font-family: var(--mono);
    font-size: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
  }
  .chain-labels span[data-active="true"] { color: var(--accent-strong); }

  .controls { display: flex; align-items: center; gap: 14px; }
  button.play {
    font-family: var(--mono);
    font-size: 13px;
    padding: 7px 14px;
    border: 1px solid var(--line);
    border-radius: 7px;
    background: var(--surface);
    color: var(--ink);
    cursor: pointer;
    min-width: 76px;
  }
  button.play:hover { border-color: var(--accent); color: var(--accent-strong); }
  button.play:focus-visible, input[type="range"]:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  input[type="range"] { flex: 1; accent-color: var(--accent); min-width: 0; }
  .readout {
    font-family: var(--mono);
    font-variant-numeric: tabular-nums;
    font-size: 13px;
    color: var(--muted);
    width: 78px;
    text-align: right;
  }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
  @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
  .card { padding: 20px 22px; display: flex; flex-direction: column; gap: 12px; }
  .card h2 {
    margin: 0;
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  .card p { margin: 0; color: var(--muted); font-size: 14px; }
  .card .stage svg { width: min(220px, 60vw); }

  pre {
    margin: 0;
    background: var(--code-bg);
    border: 1px solid var(--line);
    border-radius: 7px;
    padding: 12px 14px;
    overflow-x: auto;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.6;
  }
  .manim-card { margin-top: 16px; }
  .manim-card video {
    width: 100%;
    border: 1px solid var(--line);
    border-radius: 7px;
    background: #0E1418;
  }
  .code-scroll { max-height: 360px; overflow: auto; }
  code { font-family: var(--mono); }
  #d-output {
    display: block;
    max-height: 130px;
    overflow-y: auto;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }
  .kw { color: var(--accent-strong); }

  footer {
    margin-top: 36px;
    padding-top: 18px;
    border-top: 1px solid var(--line);
    color: var(--muted);
    font-size: 13px;
  }
  footer code { font-size: 12px; }
  a { color: var(--accent-strong); }

  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; }
  }
</style>
</head>
<body>
<main>
  <header>
    <span class="eyebrow">polymorph-py &middot; demo</span>
    <h1>Morph SVG paths in pure Python</h1>
    <p class="tagline">
      Every shape on this page was parsed, aligned, and paired by the Python library
      &mdash; the browser only mixes the prepared coordinates, exactly as
      <code>interpolate()</code> does.
    </p>
  </header>

  <section class="stage-card" aria-label="Chain morph demo">
    <div class="stage">
      <svg viewBox="0 0 100 100" role="img" aria-label="Shape morphing between a square, circle, star, and heart">
        <path id="hero-shape" class="shape" d=""></path>
      </svg>
    </div>
    <div class="chain-labels" id="chain-labels"></div>
    <div class="controls">
      <button class="play" id="hero-play" aria-label="Pause animation">pause</button>
      <input type="range" id="hero-scrub" min="0" max="1000" value="0" step="1"
             aria-label="Morph offset">
      <span class="readout" id="hero-readout">t=0.000</span>
    </div>
  </section>

  <div class="grid">
    <section class="card" aria-label="Subpath morph demo">
      <h2>Holes &amp; subpaths</h2>
      <p>
        One subpath morphs into three. The library pads the missing subpaths with
        points at each shape&rsquo;s origin, so new pieces grow out of nothing.
      </p>
      <div class="stage">
        <svg viewBox="0 0 100 100" role="img" aria-label="One square morphing into three blocks">
          <path id="multi-shape" class="shape" d=""></path>
        </svg>
      </div>
      <div class="controls">
        <input type="range" id="multi-scrub" min="0" max="1000" value="0" step="1"
               aria-label="Subpath morph offset">
        <span class="readout" id="multi-readout">t=0.000</span>
      </div>
    </section>

    <section class="card" aria-label="Live path data">
      <h2>Live path data</h2>
      <p>The <code>d</code> attribute being rendered in the hero, as you scrub:</p>
      <pre><code id="d-output"></code></pre>
      <p>Recreate it in Python:</p>
      <pre><code><span class="kw">from</span> polymorph <span class="kw">import</span> interpolate

f = interpolate([square, circle, star, heart],
                precision=<span class="kw">2</span>)
f(<span id="py-offset">0.0</span>)  <span style="opacity:.55"># &rarr; the string above</span></code></pre>
    </section>
  </div>

  <section class="card manim-card" aria-label="Manim example">
    <h2>polymorph &times; Manim</h2>
    <p>
      polymorph is not tied to the browser: here it drives a
      <a href="https://www.manim.community/">Manim</a>-rendered video, side by
      side with Manim&rsquo;s own <code>Transform</code>. A small five-pointed
      star sits with its points in the troughs of a larger one (rotated
      36&deg;) and morphs outward to fill it. The generic point-interpolating
      Transform (left) rotates the shape into place; with polymorph (right)
      the vertex pairing is yours to choose, so the star&rsquo;s points stay
      pinned in the troughs while its troughs erupt outward. polymorph&rsquo;s
      parsed data is cubic beziers &mdash; the same primitive Manim&rsquo;s
      <code>VMobject</code> uses &mdash; so the mixed coordinates map straight
      onto the screen.
    </p>
    <video id="manim-video" src="star-morph.mp4" poster="star-morph-poster.jpg"
           loop muted playsinline controls preload="metadata"
           aria-label="Manim-rendered video of a small star morphing into the star that contains it"></video>
    <p>The complete code that produced the video (<code>examples/star_morph.py</code>):</p>
    <pre class="code-scroll"><code>__MANIM_CODE__</code></pre>
  </section>

  <footer>
    Generated by <code>demo/generate.py</code> using
    <a href="https://github.com/pjfo/polymorph">polymorph-py</a>, a Python port of
    <a href="https://github.com/notoriousb1t/polymorph">polymorph-js</a>.
    Run <code>python demo/generate.py</code> to rebuild this page.
  </footer>
</main>

<script>
  const DATA = __DATA__;

  const fmt = (n) => {
    const r = Math.round(n * 100) / 100;
    return Object.is(r, -0) ? "0" : String(r);
  };

  function mix(a, b, t) {
    const out = new Array(a.length);
    for (let i = 0; i < a.length; i++) out[i] = a[i] + (b[i] - a[i]) * t;
    return out;
  }

  function render(segments) {
    let s = "";
    for (const n of segments) {
      s += (s ? " " : "") + "M " + fmt(n[0]) + " " + fmt(n[1]) + " C";
      for (let i = 2; i < n.length; i++) s += " " + fmt(n[i]);
    }
    return s;
  }

  // pairs: list of [left, right] matrices; t in [0, 1] spans the whole chain
  function chainFrame(pairs, t) {
    const h = pairs.length;
    const d = h * t;
    const i = Math.min(Math.max(Math.floor(d), 0), h - 1);
    const [left, right] = pairs[i];
    return { d: render(left.map((seg, k) => mix(seg, right[k], d - i))), segment: i, local: d - i };
  }

  // --- hero chain morph ---
  const heroShape = document.getElementById("hero-shape");
  const heroScrub = document.getElementById("hero-scrub");
  const heroReadout = document.getElementById("hero-readout");
  const heroPlay = document.getElementById("hero-play");
  const dOutput = document.getElementById("d-output");
  const pyOffset = document.getElementById("py-offset");
  const labelBox = document.getElementById("chain-labels");

  DATA.chain.names.forEach((name) => {
    const span = document.createElement("span");
    span.textContent = name;
    labelBox.appendChild(span);
  });
  const labels = Array.from(labelBox.children);

  function setHero(t) {
    const frame = chainFrame(DATA.chain.pairs, t);
    heroShape.setAttribute("d", frame.d);
    heroReadout.textContent = "t=" + t.toFixed(3);
    pyOffset.textContent = t.toFixed(3);
    dOutput.textContent = frame.d;
    const active = t >= 1 ? labels.length - 1
      : frame.local < 0.5 ? frame.segment : frame.segment + 1;
    labels.forEach((el, i) => el.setAttribute("data-active", i === active));
  }

  // --- subpath morph card ---
  const multiShape = document.getElementById("multi-shape");
  const multiScrub = document.getElementById("multi-scrub");
  const multiReadout = document.getElementById("multi-readout");
  const [multiLeft, multiRight] = DATA.subpaths;

  function setMulti(t) {
    multiShape.setAttribute("d", render(multiLeft.map((seg, k) => mix(seg, multiRight[k], t))));
    multiReadout.textContent = "t=" + t.toFixed(3);
  }

  // --- animation loop (ping-pong), paused on user scrub or reduced motion ---
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let playing = !reduceMotion;
  let t = 0;
  let direction = 1;
  let last = null;

  function tick(now) {
    if (playing) {
      if (last !== null) {
        t += direction * ((now - last) / 1000) * 0.14;
        if (t >= 1) { t = 1; direction = -1; }
        if (t <= 0) { t = 0; direction = 1; }
      }
      heroScrub.value = String(Math.round(t * 1000));
      multiScrub.value = heroScrub.value;
      setHero(t);
      setMulti(t);
    }
    last = now;
    requestAnimationFrame(tick);
  }

  function setPlaying(next) {
    playing = next;
    heroPlay.textContent = playing ? "pause" : "play";
    heroPlay.setAttribute("aria-label", playing ? "Pause animation" : "Play animation");
  }

  heroPlay.addEventListener("click", () => setPlaying(!playing));
  heroScrub.addEventListener("input", () => {
    setPlaying(false);
    t = Number(heroScrub.value) / 1000;
    setHero(t);
  });
  multiScrub.addEventListener("input", () => {
    setPlaying(false);
    setMulti(Number(multiScrub.value) / 1000);
  });

  setPlaying(playing);
  setHero(0);
  setMulti(0);
  requestAnimationFrame(tick);

  const manimVideo = document.getElementById("manim-video");
  if (manimVideo && !reduceMotion) {
    manimVideo.autoplay = true;
    manimVideo.play().catch(() => {});
  }
</script>
</body>
</html>
"""


def main() -> None:
    root = FilePath(__file__).resolve().parent.parent
    manim_source = (root / "examples" / "star_morph.py").read_text(encoding="utf-8")
    page = TEMPLATE.replace("__DATA__", build_data())
    page = page.replace("__MANIM_CODE__", html.escape(manim_source.strip()))
    out = root / "demo" / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
    main()
