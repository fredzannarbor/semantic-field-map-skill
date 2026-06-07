---
name: semantic-field-map
description: Show the conceptual landscape behind an answer without revealing chain-of-thought. A view argument selects the output — inline labeled field map (default), a rendered TOPOGRAPHIC map (continuous 2D heat-gradient + contour isolines), a 3D volume surface, or an inline emoji-grid fallback — all computed from a Gaussian-mixture field over the actual concepts in the answer. Use when the user wants responses to be more spatial, colorful, concept-aware, or explicitly asks for semantic field/terrain/topographic/volume maps.
argument-hint: "[field|topographic|volume|terrain-text|volume-text] [sigma=… levels=… elev=… azim=… no-labels] [off]"
---

# Semantic Field Map

Before answering, prepend a Semantic Field Map unless the user disables it.

Do not reveal chain-of-thought, hidden reasoning, internal deliberations, or intermediate calculations. The map is an approximate semantic field: the concepts most relevant to the answer.

## Options (skill arguments)

The skill takes an optional **view** keyword plus optional tuning parameters. With no argument, render the default `field` view. The keywords below select which map to produce; everything after the keyword passes through to the renderer.

| view keyword | output | how to produce |
| --- | --- | --- |
| `field` (default) | inline labeled diagram (text) | hand-place the labeled node diagram (see below) |
| `topographic` · `topo` · `contour` · `2d` | continuous 2D topographic **PNG** | `topographic_map.py --mode topo` |
| `volume` · `surface` · `3d` | 3D terrain surface **PNG** | `topographic_map.py --mode surface` |
| `terrain-text` · `volume-text` · `grid` | inline emoji-grid (no image) | `semantic_field.py --view terrain` / `--view volume` |

Tuning parameters (pass through to the PNG renderer): `sigma=` (spread; smaller ⇒ sharper, more separated hills), `levels=` (isoline count), `res=`, `title="…"`, `no-labels`; 3D also takes `elev=` / `azim=` (view angles). `off` / `disable` stops prepending maps for the rest of the session.

Examples:
- `topographic` → render the 2D topographic PNG.
- `volume sigma=0.13 azim=-50` → render the 3D surface, tighter hills, rotated view.
- *(no argument)* → inline field map.

The image views are the richest; pick them whenever image output is possible. The inline views are the fallback when it isn't.

## Choosing the concepts (read first)

Every view below is built from a small set of concepts. **The labels MUST be the actual, specific nouns and phrases from the answer's own subject matter** — the real things the response is about. For an answer on photosynthesis: `chloroplast`, `Calvin cycle`, `ATP`, `stomata`. For an answer on a refactor: the real module/function names.

- **Never** use generic scaffolding labels like "Main Concept", "primary action", "context field", "adjacent idea". Those are placeholders only.
- Pick 3–6 concepts that genuinely organize the answer.
- `x`, `y` in `[0, 1]`: position by relatedness — concepts that belong together sit near each other; the dominant idea near the center.
- `weight` in `[0, 1]`: how central the concept is to the answer. The heaviest becomes the peak / center of gravity.

The Gaussian-mixture field is `f(x,y) = Σ wᵢ·exp(−((x−xᵢ)² + (y−yᵢ)²) / 2σ²)`. Curved nested contours and separate hills are real level sets of this field — not decoration.

## Map views

### Topographic map — continuous 2D (rendered PNG, richest)

A real topographic map: a continuous heat-gradient surface (deep-water blue → green → yellow → orange → red peaks) with smooth curved **contour isolines** over it. Multiple concepts produce multiple hills, each with its own nested closed contours. Prefer this whenever image output is possible.

```bash
echo '[
  {"label": "chloroplast",  "x": 0.50, "y": 0.52, "weight": 1.00},
  {"label": "Calvin cycle", "x": 0.22, "y": 0.34, "weight": 0.80},
  {"label": "ATP",          "x": 0.76, "y": 0.30, "weight": 0.66},
  {"label": "stomata",      "x": 0.32, "y": 0.78, "weight": 0.55}
]' | uv run python scripts/topographic_map.py --mode topo --out /tmp/semantic_field/topo.png
```

### Volume — 3D surface (rendered PNG)

The same computed field as a continuous curved 3D terrain surface, in the same heat gradient, with contour isolines on the floor and concept names floating above the surface on short dashed leader lines (projected from each peak, spread across two tiers so they never collide or get occluded).

```bash
... | uv run python scripts/topographic_map.py --mode surface --out /tmp/semantic_field/volume.png
```

Flags (both modes): `--demo`, `--sigma` (smaller ⇒ sharper, more separated hills), `--levels` (isoline count), `--res`, `--no-labels`, `--title`; 3D adds `--elev` / `--azim` view angles. Requires the project env (`uv run`) so `matplotlib`/`numpy` resolve — both are already installed; **do not install anything**. After rendering, display/attach the PNG to the user.

### Inline field map (no image needed)

A compact labeled diagram for quick, text-only context. Use real concept labels here too.

```text
                            🟣
                       <abstract idea>
                            │

🔵 ───────────────── ⭐ ───────────────── 🟢
<context>          <core>            <primary concept>

                            │
                            🟡
                       <adjacent idea>

                            🔴
                       <minor idea>
```

### Inline text terrain/volume (fallback only)

If no code-execution or image output is available, compute the same field by hand on a small grid with `scripts/semantic_field.py` (pure stdlib, emits a banded emoji grid: `python3 scripts/semantic_field.py --view both`). This is a coarse fallback for the rendered PNGs above — do not fabricate a grid that isn't the computed field.

## Rules

- Labels are always the real, specific concepts from the answer — never generic placeholders. This is the most important rule.
- Default to the colorful emoji / vibrant heat gradient. Only use plain markers if the user explicitly asks for a plain/no-emoji map.
- Honor the view argument from Options above: an explicit keyword (`topographic`, `volume`, etc.) overrides the default `field` view.
- When the user says "topographic", "contour", or "terrain map" and image output is available, render the 2D topographic PNG — that is the look they mean. Use the 3D surface when they ask for volume / 3D.
- All gradient views must be **computed** from the field, never hand-drawn.
- Keep it compact: the inline map plus a short one-line center-of-gravity note, or a single rendered image.
- Do not include private deliberation, scratch work, hidden calculations, or tool-only details.
- If the user disables maps, answer normally without mentioning the skill.
