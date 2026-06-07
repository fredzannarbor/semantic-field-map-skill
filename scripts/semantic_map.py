#!/usr/bin/env python3
"""Unified semantic field / activation map generator.

One computed pipeline, several views. Every view is built from a real
Gaussian-mixture scalar field over a set of concepts; nothing is hand-drawn.

Views (--view):
  topo     Continuous 2D topographic PNG: interpolated heat-gradient surface
           (blue->green->yellow->orange->red) with smooth contour isolines.
  surface  3D volume surface PNG: continuous curved terrain in the same
           gradient, with concept names floating above on dashed leaders
           (projected to 2D so they never collide or get occluded).
  clouds   3D semi-transparent concept clouds PNG (Activation Field style).
  grid     Inline emoji text maps (terrain + volume), no image output.

Concepts come from one of:
  * hand-placed JSON (stdin or --concepts FILE): [{"label","x","y","weight"}],
    with x, y, weight in [0, 1]; optional "z" for clouds.
  * --derive: weights and coordinates DERIVED from a visible prompt+answer pair
    via TF-IDF + cosine similarity + PCA (requires scikit-learn). Provide the
    text with --text-json FILE ({"prompt","answer","concepts":[...]}), else the
    built-in demo text is used.

Labels MUST be the actual concepts from the answer, never generic placeholders.

Transparency: this only builds an interpretive concept map from visible text /
inputs. It does not expose chain-of-thought, hidden reasoning, private
deliberation, intermediate calculations, model state, or neural activations.

Run inside the project env so deps resolve, e.g.:
    uv run python scripts/semantic_map.py --demo --view topo --out /tmp/topo.png
"""
from __future__ import annotations

import argparse
import json
import sys
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")  # headless render
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Vibrant topographic heat gradient: deep-water blue -> land -> hot peaks.
TERRAIN_STOPS = [
    "#143a7b", "#1f6fb2", "#2bb2a3", "#5fc85a", "#bfe04a",
    "#f2e34a", "#f3a52e", "#e2592a", "#b01b1b",
]
TERRAIN_CMAP = LinearSegmentedColormap.from_list("semantic_terrain", TERRAIN_STOPS, N=256)

# Cool -> warm emoji bands for the inline (no-image) grid view.
BANDS = ["🟦", "🟩", "🟨", "🟧", "🟥"]
PEAK = "⭐"

# Hand-placed demo (real nouns on purpose; never use generic placeholders).
DEMO_CONCEPTS = [
    {"label": "chloroplast", "x": 0.50, "y": 0.50, "weight": 1.00},
    {"label": "Calvin cycle", "x": 0.70, "y": 0.40, "weight": 0.78},
    {"label": "thylakoid", "x": 0.30, "y": 0.62, "weight": 0.72},
    {"label": "chlorophyll", "x": 0.22, "y": 0.30, "weight": 0.62},
    {"label": "ATP", "x": 0.78, "y": 0.66, "weight": 0.60},
    {"label": "glucose", "x": 0.82, "y": 0.20, "weight": 0.56},
    {"label": "NADPH", "x": 0.58, "y": 0.80, "weight": 0.50},
    {"label": "stomata", "x": 0.18, "y": 0.82, "weight": 0.46},
    {"label": "photolysis", "x": 0.40, "y": 0.16, "weight": 0.44},
    {"label": "rubisco", "x": 0.88, "y": 0.50, "weight": 0.40},
]

# Demo text for --derive.
DEMO_TEXT = {
    "prompt": "How should a small independent publisher decide whether to launch a "
              "short series of AI-assisted books about future space warfare?",
    "answer": (
        "A small independent publisher should treat an AI-assisted space warfare series "
        "as a focused market experiment rather than a broad publishing bet. The strongest "
        "case combines a defensible editorial angle, credible military and space-policy "
        "sources, fast production workflows, and clear discoverability through metadata, "
        "series branding, newsletter promotion, and backlist cross-selling. Avoid generic "
        "futurism; test narrow titles with strong reader intent, visible search demand, "
        "and a low-cost production path."
    ),
    "concepts": [
        "independent publisher", "AI-assisted books", "space warfare", "market experiment",
        "editorial angle", "credible sources", "production workflows", "discoverability",
        "metadata strategy", "series branding", "newsletter promotion", "backlist cross-selling",
        "generic futurism", "reader intent", "search demand", "low-cost production",
    ],
}


# --------------------------------------------------------------------------- #
# Concept sourcing
# --------------------------------------------------------------------------- #
def _minmax(arr):
    arr = np.asarray(arr, dtype=float)
    span = (arr.max() - arr.min()) or 1.0
    return (arr - arr.min()) / span


def derive_from_text(prompt, answer, concept_labels, top_n=10):
    """Derive concept weights + coordinates from visible text (TF-IDF + PCA)."""
    try:
        from sklearn.decomposition import PCA
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit("--derive needs scikit-learn (pip install scikit-learn)") from exc

    docs = [prompt, answer] + list(concept_labels)
    matrix = TfidfVectorizer(lowercase=True, ngram_range=(1, 3),
                             stop_words="english").fit_transform(docs)
    prompt_sim = cosine_similarity(matrix[2:], matrix[0]).ravel()
    answer_sim = cosine_similarity(matrix[2:], matrix[1]).ravel()
    raw = 0.45 * prompt_sim + 0.55 * answer_sim
    weights = _minmax(raw)
    coords = PCA(n_components=3, random_state=42).fit_transform(matrix.toarray())[2:]

    xs, ys, zs = _minmax(coords[:, 0]), _minmax(coords[:, 1]), _minmax(coords[:, 2])
    rows = [
        {"label": lbl, "x": float(x), "y": float(y), "z": float(z), "weight": float(w)}
        for lbl, x, y, z, w in zip(concept_labels, xs, ys, zs, weights)
    ]
    rows.sort(key=lambda r: r["weight"], reverse=True)
    return rows[:top_n]


def load_concepts(args):
    if args.derive:
        text = DEMO_TEXT
        if args.text_json:
            with open(args.text_json, encoding="utf-8") as fh:
                text = json.load(fh)
        return derive_from_text(text["prompt"], text["answer"], text["concepts"])
    if args.demo:
        return [dict(c) for c in DEMO_CONCEPTS]
    if args.concepts:
        with open(args.concepts, encoding="utf-8") as fh:
            return json.load(fh)
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else [dict(c) for c in DEMO_CONCEPTS]
    return [dict(c) for c in DEMO_CONCEPTS]


# --------------------------------------------------------------------------- #
# Field computation
# --------------------------------------------------------------------------- #
def compute_field(concepts, res, sigma, aspect=1.0):
    xs = np.linspace(0.0, 1.0, res)
    ys = np.linspace(0.0, 1.0, res)
    gx, gy = np.meshgrid(xs, ys)
    field = np.zeros_like(gx)
    denom = 2.0 * sigma * sigma
    for c in concepts:
        dx = gx - float(c["x"])
        dy = (gy - float(c["y"])) * aspect
        field += float(c["weight"]) * np.exp(-(dx * dx + dy * dy) / denom)
    return gx, gy, field


def field_at(concepts, x, y, sigma):
    denom = 2.0 * sigma * sigma
    total = 0.0
    for c in concepts:
        dx = x - float(c["x"])
        dy = y - float(c["y"])
        total += float(c["weight"]) * np.exp(-(dx * dx + dy * dy) / denom)
    return total


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #
def _save(fig, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def render_topo(concepts, args):
    """Continuous 2D topographic map: smooth heat-gradient fill + isolines."""
    gx, gy, field = compute_field(concepts, args.res, args.sigma)
    levels = np.linspace(float(field.min()), float(field.max()), args.levels)

    fig, ax = plt.subplots(figsize=(args.size, args.size), dpi=args.dpi)
    ax.imshow(field, extent=(0, 1, 0, 1), origin="lower", cmap=TERRAIN_CMAP,
              interpolation="bicubic", aspect="equal")
    ax.contour(gx, gy, field, levels=levels, colors="#0b1d33",
               linewidths=0.7, alpha=0.5, antialiased=True)

    if not args.no_labels:
        for c in concepts:
            cx, cy = float(c["x"]), float(c["y"])
            ax.plot(cx, cy, "o", ms=4, mfc="white", mec="#0b1d33", mew=0.8)
            ha = "right" if cx > 0.7 else "left"
            dx = -6 if cx > 0.7 else 6
            dy = -10 if cy > 0.85 else 5
            va = "top" if cy > 0.85 else "bottom"
            ax.annotate(c["label"], (cx, cy), textcoords="offset points",
                        xytext=(dx, dy), ha=ha, va=va, fontsize=8,
                        color="#0b1d33", weight="bold")
        j, i = np.unravel_index(int(np.argmax(field)), field.shape)
        ax.plot(gx[j, i], gy[j, i], "*", ms=16, mfc="#fff3b0", mec="#0b1d33", mew=0.8)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    if args.title:
        ax.set_title(args.title, fontsize=11, color="#0b1d33", weight="bold")
    _save(fig, args.out)
    return args.out


def _float_labels_3d(fig, ax, concepts, sigma):
    """2D annotations floating above the 3D view, one short dashed leader each."""
    from mpl_toolkits.mplot3d import proj3d
    fig.canvas.draw()
    proj = ax.get_proj()
    pts = []
    for c in concepts:
        cx, cy = float(c["x"]), float(c["y"])
        zs = field_at(concepts, cx, cy, sigma)
        x2, y2, _ = proj3d.proj_transform(cx, cy, zs, proj)
        pts.append((x2, y2, c["label"]))
    pts.sort(key=lambda p: p[0])
    n = len(pts)
    fracs = [0.5] if n == 1 else list(np.linspace(0.035, 0.965, n))
    for i, (x2, y2, label) in enumerate(pts):
        ytext = 0.90 if (i % 2) else 0.80
        ax.annotate(label, xy=(x2, y2), xycoords="data",
                    xytext=(fracs[i], ytext), textcoords=ax.transAxes,
                    ha="center", va="bottom", fontsize=7, color="#0b1d33", weight="bold",
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="#0b1d33", alpha=0.45,
                                    linestyle=(0, (4, 3)), shrinkA=1, shrinkB=2),
                    annotation_clip=False)


def render_surface(concepts, args):
    """3D volume: continuous curved terrain surface with floating labels."""
    res = min(args.res, 220)
    gx, gy, field = compute_field(concepts, res, args.sigma)
    levels = np.linspace(float(field.min()), float(field.max()), args.levels)

    fig = plt.figure(figsize=(args.size, args.size), dpi=args.dpi)
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(gx, gy, field, cmap=TERRAIN_CMAP, linewidth=0,
                    antialiased=True, rcount=160, ccount=160)
    floor = float(field.min()) - 0.15 * (float(field.max()) - float(field.min()))
    ax.contour(gx, gy, field, levels=levels, zdir="z", offset=floor,
               colors="#0b1d33", linewidths=0.5, alpha=0.4)
    ax.set_zlim(floor, float(field.max()) * 1.05)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.view_init(elev=args.elev, azim=args.azim)
    ax.set_box_aspect((1, 1, 0.62))
    try:
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        ax.zaxis.pane.set_visible(False)
        ax.grid(False)
    except Exception:
        pass
    if args.title:
        ax.set_title(args.title, fontsize=11, color="#0b1d33", weight="bold")
    if not args.no_labels:
        _float_labels_3d(fig, ax, concepts, args.sigma)
    _save(fig, args.out)
    return args.out


def render_clouds(concepts, args):
    """3D semi-transparent concept clouds (Activation Field style)."""
    rng = np.random.default_rng(7)
    fig = plt.figure(figsize=(args.size * 1.15, args.size), dpi=args.dpi)
    ax = fig.add_subplot(111, projection="3d")
    colors = TERRAIN_CMAP(np.linspace(0.2, 0.95, max(len(concepts), 1)))
    order = sorted(range(len(concepts)), key=lambda k: -float(concepts[k]["weight"]))
    for ci, k in enumerate(order):
        c = concepts[k]
        cx, cy = float(c["x"]), float(c["y"])
        cz = float(c.get("z", c["weight"]))
        w = float(c["weight"])
        npts = int(220 + 620 * w)
        spread = 0.035 + 0.12 * (1.0 - w)
        pts = rng.normal([cx, cy, cz], spread, size=(npts, 3))
        ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=10 + 18 * w,
                   color=colors[ci], alpha=0.06 + 0.12 * w, depthshade=True)
        ax.scatter([cx], [cy], [cz], s=120 + 360 * w, color=colors[ci],
                   edgecolor="black", depthshade=False)
        if not args.no_labels:
            ax.text(cx, cy, cz, f"  {c['label']}", fontsize=8, color="#0b1d33", weight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.view_init(elev=27, azim=40)
    if args.title:
        ax.set_title(args.title, fontsize=11, color="#0b1d33", weight="bold")
    _save(fig, args.out)
    return args.out


def render_grid(concepts, args):
    """Inline emoji terrain + volume maps (no image)."""
    w, h = args.width, args.height

    def banded(value, lo, hi):
        v = (value - lo) / ((hi - lo) or 1.0)
        return min(int(v * len(BANDS)), len(BANDS) - 1)

    # Terrain: build a w-wide, h-tall grid.
    xs = np.linspace(0, 1, w)
    ys = np.linspace(0, 1, h)
    grid = np.zeros((h, w))
    denom = 2.0 * args.sigma * args.sigma
    for j, sy in enumerate(ys):
        for i, sx in enumerate(xs):
            tot = 0.0
            for c in concepts:
                dx = sx - float(c["x"])
                dy = (sy - float(c["y"])) * 2.0
                tot += float(c["weight"]) * np.exp(-(dx * dx + dy * dy) / denom)
            grid[j, i] = tot
    lo, hi = grid.min(), grid.max()
    pj, pi = np.unravel_index(int(np.argmax(grid)), grid.shape)

    lines = ["Semantic Terrain — computed field (warm = high relevance)", ""]
    for j in range(h):
        lines.append("".join(
            PEAK if (j, i) == (pj, pi) else BANDS[banded(grid[j, i], lo, hi)]
            for i in range(w)))
    lines += ["", "🟥 high · 🟧 · 🟨 · 🟩 · 🟦 low   ⭐ center of gravity", ""]

    # Volume: per-column elevation relief.
    col = (grid - lo) / ((hi - lo) or 1.0)
    col_val = col.max(axis=0)
    bars = [int(round(v * h)) for v in col_val]
    peak_col = int(np.argmax(col_val))
    lines += ["Semantic Volume — elevation relief (height = relevance)", ""]
    for r in range(h - 1, -1, -1):
        row = []
        for i in range(w):
            if bars[i] > r:
                row.append(PEAK if (r == bars[i] - 1 and i == peak_col)
                           else BANDS[min(int(r / max(h - 1, 1) * len(BANDS)), len(BANDS) - 1)])
            else:
                row.append("  ")
        lines.append("".join(row).rstrip())
    legend = "  ".join(f"{n+1}. {concepts[k]['label']}" for n, k in enumerate(
        sorted(range(len(concepts)), key=lambda k: -float(concepts[k]["weight"]))))
    lines += ["", legend]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(description="Unified semantic field / activation map generator.")
    p.add_argument("--view", choices=["topo", "surface", "clouds", "grid"], default="topo")
    p.add_argument("--concepts", help="hand-placed concepts JSON file (else stdin / --demo)")
    p.add_argument("--demo", action="store_true", help="use the built-in photosynthesis concept set")
    p.add_argument("--derive", action="store_true",
                   help="derive concepts from a prompt+answer pair (TF-IDF + PCA)")
    p.add_argument("--text-json", help="JSON with {prompt, answer, concepts} for --derive")
    p.add_argument("--out", default="/tmp/semantic_field/map.png")
    p.add_argument("--res", type=int, default=400, help="grid resolution per axis (image views)")
    p.add_argument("--levels", type=int, default=16, help="number of contour levels")
    p.add_argument("--sigma", type=float, default=0.20, help="Gaussian spread")
    p.add_argument("--size", type=float, default=6.0, help="figure size in inches")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--title", default="Semantic Map")
    p.add_argument("--no-labels", action="store_true")
    p.add_argument("--elev", type=float, default=42.0, help="3D view elevation")
    p.add_argument("--azim", type=float, default=-58.0, help="3D view azimuth")
    p.add_argument("--width", type=int, default=21, help="grid view columns")
    p.add_argument("--height", type=int, default=11, help="grid view rows")
    args = p.parse_args(argv)

    concepts = load_concepts(args)
    if args.view == "grid":
        print(render_grid(concepts, args))
        return
    renderer = {"topo": render_topo, "surface": render_surface, "clouds": render_clouds}[args.view]
    print(renderer(concepts, args))


if __name__ == "__main__":
    main()
