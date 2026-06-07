#!/usr/bin/env python3
"""Render a computed TOPOGRAPHIC semantic map.

This computes a real scalar field (a Gaussian mixture over the concepts you
place) on a high-resolution grid, then renders it the way a topographic map
is rendered: a vibrant heat-gradient fill (contourf) overlaid with contour
isolines (contour). The curved, nested contour lines are genuine level sets
of the computed field — not drawn by hand.

    f(x, y) = sum_i  w_i * exp(-((x - x_i)^2 + (y - y_i)^2) / (2 sigma^2))

Run inside the project env so matplotlib/numpy resolve:

    uv run python scripts/topographic_map.py --demo --out /tmp/semantic_field/topo.png

Concepts JSON (stdin or --concepts FILE):
    [{"label": "primary action", "x": 0.5, "y": 0.5, "weight": 1.0}, ...]
x, y, weight in [0, 1]. Use --demo for the built-in field-map concept set.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")  # headless render
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Vibrant heat gradient: deep-water blue -> land greens/yellows -> hot peaks.
TERRAIN_STOPS = [
    "#143a7b",  # deep water
    "#1f6fb2",  # shallow water
    "#2bb2a3",  # coast / teal
    "#5fc85a",  # lowland green
    "#bfe04a",  # green-yellow
    "#f2e34a",  # yellow plateau
    "#f3a52e",  # orange foothills
    "#e2592a",  # high ground
    "#b01b1b",  # peak
]
TERRAIN_CMAP = LinearSegmentedColormap.from_list("semantic_terrain", TERRAIN_STOPS, N=256)

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


def load_concepts(args):
    if args.demo:
        return DEMO_CONCEPTS
    if args.concepts:
        with open(args.concepts, encoding="utf-8") as fh:
            return json.load(fh)
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        return json.loads(raw) if raw else DEMO_CONCEPTS
    return DEMO_CONCEPTS


def compute_field(concepts, res, sigma):
    """Vectorized Gaussian-mixture field on a res x res grid over [0,1]^2."""
    xs = np.linspace(0.0, 1.0, res)
    ys = np.linspace(0.0, 1.0, res)
    gx, gy = np.meshgrid(xs, ys)
    field = np.zeros_like(gx)
    denom = 2.0 * sigma * sigma
    for c in concepts:
        dx = gx - float(c["x"])
        dy = gy - float(c["y"])
        field += float(c["weight"]) * np.exp(-(dx * dx + dy * dy) / denom)
    return gx, gy, field


def field_at(concepts, x, y, sigma):
    """Field height at a single point (for placing 3D labels)."""
    denom = 2.0 * sigma * sigma
    total = 0.0
    for c in concepts:
        dx = x - float(c["x"])
        dy = y - float(c["y"])
        total += float(c["weight"]) * np.exp(-(dx * dx + dy * dy) / denom)
    return total


def render_topo(concepts, args):
    """Continuous 2D topographic map: smooth heat-gradient fill + contour isolines."""
    gx, gy, field = compute_field(concepts, args.res, args.sigma)
    levels = np.linspace(float(field.min()), float(field.max()), args.levels)

    fig, ax = plt.subplots(figsize=(args.size, args.size), dpi=args.dpi)
    # Continuous heat-gradient surface (smooth, no banding) via interpolated raster.
    ax.imshow(field, extent=(0, 1, 0, 1), origin="lower", cmap=TERRAIN_CMAP,
              interpolation="bicubic", aspect="equal")
    # Smooth curved contour isolines drawn over the continuous surface.
    ax.contour(gx, gy, field, levels=levels, colors="#0b1d33",
               linewidths=0.7, alpha=0.5, antialiased=True)

    if not args.no_labels:
        for c in concepts:
            cx, cy = float(c["x"]), float(c["y"])
            ax.plot(cx, cy, "o", ms=4, mfc="white", mec="#0b1d33", mew=0.8)
            # Edge-aware placement so labels don't run off the frame or collide.
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


def render_surface(concepts, args):
    """3D volume: continuous curved terrain surface in the same heat gradient."""
    res = min(args.res, 220)  # plot_surface is dense; keep mesh manageable
    gx, gy, field = compute_field(concepts, res, args.sigma)
    levels = np.linspace(float(field.min()), float(field.max()), args.levels)

    fig = plt.figure(figsize=(args.size, args.size), dpi=args.dpi)
    ax = fig.add_subplot(111, projection="3d")
    # Continuous smooth curved surface.
    ax.plot_surface(gx, gy, field, cmap=TERRAIN_CMAP, linewidth=0,
                    antialiased=True, rcount=160, ccount=160)
    # Contour isolines projected onto the floor for topographic context.
    floor = float(field.min()) - 0.15 * (float(field.max()) - float(field.min()))
    ax.contour(gx, gy, field, levels=levels, zdir="z", offset=floor,
               colors="#0b1d33", linewidths=0.5, alpha=0.4)
    ax.set_zlim(floor, float(field.max()) * 1.05)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.view_init(elev=args.elev, azim=args.azim)
    ax.set_box_aspect((1, 1, 0.62))
    try:  # hide the bounding panes for a clean floating-terrain look
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        ax.zaxis.pane.set_visible(False)
        ax.grid(False)
    except Exception:
        pass
    if args.title:
        ax.set_title(args.title, fontsize=11, color="#0b1d33", weight="bold")

    if not args.no_labels:
        _float_labels_3d(fig, ax, concepts, field, args.sigma)

    _save(fig, args.out)
    return args.out


def _float_labels_3d(fig, ax, concepts, field, sigma):
    """Place concept names as 2D annotations floating above the 3D view.

    Each peak's 3D position is projected to the 2D screen, then its name is
    parked in a row above the plot (spread by screen-x, alternating two tiers)
    with a thin leader line back to the peak. 2D annotations draw on top of the
    surface, so labels are never occluded; spreading them prevents collisions.
    """
    from mpl_toolkits.mplot3d import proj3d

    fig.canvas.draw()  # finalize the projection before reading it
    proj = ax.get_proj()

    pts = []
    for k, c in enumerate(concepts):
        cx, cy = float(c["x"]), float(c["y"])
        zs = field_at(concepts, cx, cy, sigma)
        x2, y2, _ = proj3d.proj_transform(cx, cy, zs, proj)
        pts.append((x2, y2, c["label"]))

    pts.sort(key=lambda p: p[0])  # left-to-right by screen x
    n = len(pts)
    fracs = [0.5] if n == 1 else list(np.linspace(0.035, 0.965, n))
    for i, (x2, y2, label) in enumerate(pts):
        # Park labels low in the sky just above the surface so leaders stay short;
        # two tiers give horizontal breathing room.
        ytext = 0.90 if (i % 2) else 0.80
        ax.annotate(
            label,
            xy=(x2, y2), xycoords="data",
            xytext=(fracs[i], ytext), textcoords=ax.transAxes,
            ha="center", va="bottom", fontsize=7, color="#0b1d33", weight="bold",
            arrowprops=dict(arrowstyle="-", lw=0.4, color="#0b1d33", alpha=0.45,
                            linestyle=(0, (4, 3)), shrinkA=1, shrinkB=2),
            annotation_clip=False,
        )


def _save(fig, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def main(argv=None):
    p = argparse.ArgumentParser(description="Render a computed topographic semantic map.")
    p.add_argument("--concepts", help="JSON file of concepts; default: stdin or --demo")
    p.add_argument("--demo", action="store_true", help="use the built-in field-map concept set")
    p.add_argument("--mode", choices=["topo", "surface"], default="topo",
                   help="topo = continuous 2D topographic map; surface = 3D volume")
    p.add_argument("--out", default="/tmp/semantic_field/topographic.png")
    p.add_argument("--res", type=int, default=400, help="grid resolution per axis")
    p.add_argument("--levels", type=int, default=16, help="number of contour levels")
    p.add_argument("--sigma", type=float, default=0.20, help="Gaussian spread")
    p.add_argument("--size", type=float, default=6.0, help="figure size in inches")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument("--title", default="Semantic Topographic Map")
    p.add_argument("--no-labels", action="store_true", help="omit concept labels/markers")
    p.add_argument("--elev", type=float, default=42.0, help="3D view elevation angle")
    p.add_argument("--azim", type=float, default=-58.0, help="3D view azimuth angle")
    args = p.parse_args(argv)

    concepts = load_concepts(args)
    path = render_surface(concepts, args) if args.mode == "surface" else render_topo(concepts, args)
    print(path)


if __name__ == "__main__":
    main()
