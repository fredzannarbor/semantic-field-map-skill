# Activation Field / Semantic Field Map Skill

A portable markdown skill for adding colorful semantic-field visualizations to LLM responses without exposing chain-of-thought.

The skill reframes an answer as emerging from an approximate semantic activation field: a small map of concepts most relevant to the response.

## What it does

When an LLM receives a prompt, it can display a compact visual map of the conceptual regions likely to shape the answer. This is an interpretive semantic visualization, not a transcript of model internals.

## Transparency notice

Activation Field maps do **not** reveal chain-of-thought, hidden reasoning, private deliberation, intermediate calculations, proprietary model state, or neural activations. They show only a high-level conceptual map intended to improve readability and understanding.

## Files

- `SEMANTIC_FIELD_MAP_SKILL.md` — portable base skill.
- `src/generate_activation_field_examples.py` — parameterized Python demo generator.
- `examples/` — generated 2-D contour, 3-D volume, and 3-D semantic cloud examples.

## Visualization modes

- `emoji_ascii` — default colorful markdown map using emoji, spacing, and spatial layout.
- `contour_2d` — optional derived-value 2-D activation contour.
- `volume_3d` — optional labeled 3-D semantic volume.
- `semantic_clouds` — optional semi-transparent 3-D activation clouds.

## Example prompt

> How should a small independent publisher decide whether to launch a short series of AI-assisted books about future space warfare?

## Default behavior

The default map style is `emoji_ascii`, the first portable emoji-driven version. Image-based maps are advanced options for demos, reports, notebooks, or environments where generated PNGs are useful.
