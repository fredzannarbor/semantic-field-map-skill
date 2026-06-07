#!/usr/bin/env python3
"""Compute a semantic gradient map.

This is NOT ASCII art. It places concept nodes at (x, y) with a weight,
evaluates a real Gaussian-mixture scalar field on a grid, normalizes it,
and bands the result into a colored gradient. The terrain view is the
top-down field; the volume view is an elevation relief computed from the
same field. Output is deterministic given the same concept set.

Field:   f(x, y) = sum_i  w_i * exp(-((x-x_i)^2 + a^2 (y-y_i)^2) / (2 sigma^2))
         where `a` (--aspect) corrects for the ~2:1 width:height of an emoji
         cell so circular bumps render visually circular.

Concepts JSON (stdin or --concepts FILE):
    [{"label": "primary action", "x": 0.5, "y": 0.5, "weight": 1.0}, ...]
x, y, weight are in [0, 1]. Omit / pass --demo for the default field-map set.

Usage:
    python semantic_field.py --demo --view both
    echo '[{"label":"A","x":0.3,"y":0.4,"weight":1}]' | python semantic_field.py --view terrain
"""
from __future__ import annotations

import argparse
import json
import math
import sys

# Cool -> warm gradient bands (low relevance -> high relevance).
BANDS = ["🟦", "🟩", "🟨", "🟧", "🟥"]
PEAK = "⭐"

# Demo uses real, specific nouns on purpose: labels should always be the actual
# concepts in the answer, never generic placeholders like "Main Concept".
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


def compute_field(concepts, width, height, sigma, aspect):
    """Evaluate the Gaussian-mixture field on a width x height grid."""
    field = [[0.0] * width for _ in range(height)]
    denom = 2.0 * sigma * sigma
    for j in range(height):
        sy = j / (height - 1) if height > 1 else 0.0
        for i in range(width):
            sx = i / (width - 1) if width > 1 else 0.0
            total = 0.0
            for c in concepts:
                dx = sx - c["x"]
                dy = (sy - c["y"]) * aspect
                total += c["weight"] * math.exp(-(dx * dx + dy * dy) / denom)
            field[j][i] = total
    return field


def normalize(field):
    flat = [v for row in field for v in row]
    lo, hi = min(flat), max(flat)
    span = (hi - lo) or 1.0
    return [[(v - lo) / span for v in row] for row in field]


def band_index(value, n=len(BANDS)):
    """Map a normalized value in [0,1] to a band index."""
    idx = int(value * n)
    return min(idx, n - 1)


def argmax2d(field):
    best = (0, 0)
    best_v = float("-inf")
    for j, row in enumerate(field):
        for i, v in enumerate(row):
            if v > best_v:
                best_v, best = v, (j, i)
    return best


def render_terrain(norm):
    """Top-down banded scalar field. Peak marked with a star."""
    pj, pi = argmax2d(norm)
    lines = ["Semantic Terrain — computed scalar field (top-down; warm = high relevance)", ""]
    for j, row in enumerate(norm):
        cells = []
        for i, v in enumerate(row):
            cells.append(PEAK if (j, i) == (pj, pi) else BANDS[band_index(v)])
        lines.append("".join(cells))
    lines.append("")
    lines.append("🟥 high · 🟧 · 🟨 · 🟩 · 🟦 low   ⭐ peak (center of gravity)")
    return "\n".join(lines)


def render_volume(norm):
    """Elevation relief computed from the field: per-column height bars,
    colored by elevation. This is a real heightmap, not a drawing."""
    height = len(norm)
    width = len(norm[0])
    # Column elevation = peak field value down that column.
    col_val = [max(norm[j][i] for j in range(height)) for i in range(width)]
    bars = [int(round(v * height)) for v in col_val]
    peak_col = max(range(width), key=lambda i: col_val[i])

    lines = ["Semantic Volume — elevation relief computed from the field (height = relevance)", ""]
    for r in range(height - 1, -1, -1):  # top row first
        cells = []
        for i in range(width):
            if bars[i] > r:
                if r == bars[i] - 1 and i == peak_col:
                    cells.append(PEAK)
                else:
                    # Color by this cell's elevation fraction -> banded.
                    cells.append(BANDS[band_index(r / max(height - 1, 1))])
            else:
                cells.append("  ")  # empty sky (two spaces ~ one emoji width)
        lines.append("".join(cells).rstrip())
    lines.append("")
    lines.append("⭐ summit · warm = high ground · cool = foothills")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="Compute a semantic gradient map.")
    p.add_argument("--concepts", help="JSON file of concepts; default: stdin or --demo")
    p.add_argument("--demo", action="store_true", help="use the built-in field-map concept set")
    p.add_argument("--view", choices=["terrain", "volume", "both"], default="both")
    p.add_argument("--width", type=int, default=21)
    p.add_argument("--height", type=int, default=11)
    p.add_argument("--sigma", type=float, default=0.22)
    p.add_argument("--aspect", type=float, default=2.0,
                   help="vertical scale correcting emoji cell aspect (~2:1)")
    args = p.parse_args(argv)

    if args.demo:
        concepts = DEMO_CONCEPTS
    elif args.concepts:
        with open(args.concepts, encoding="utf-8") as fh:
            concepts = json.load(fh)
    elif not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        concepts = json.loads(raw) if raw else DEMO_CONCEPTS
    else:
        concepts = DEMO_CONCEPTS

    field = compute_field(concepts, args.width, args.height, args.sigma, args.aspect)
    norm = normalize(field)

    out = []
    if args.view in ("terrain", "both"):
        out.append(render_terrain(norm))
    if args.view in ("volume", "both"):
        out.append(render_volume(norm))
    print("\n\n".join(out))


if __name__ == "__main__":
    main()
