# Activation Field / Semantic Field Map Skill v1.1

## Purpose

Prepend an answer with a compact visualization of the conceptual landscape relevant to the response.

## Activation

When the model receives a user prompt, identify a small set of relevant conceptual regions likely to shape the response. Present these as an approximate Activation Field: a compact visual summary of the concepts most strongly associated with the answer.

This is not a literal trace of model internals. It does not include chain-of-thought, hidden reasoning, private deliberation, intermediate calculations, proprietary model state, or neural activations.

## Parameters

```yaml
activation_field:
  enabled: true
  map_style: emoji_ascii
  max_concepts: 8
  include_weights: optional
  include_notice: true
  compact: true
```

## Default Visualization

```text
                     🟣 ABSTRACT FRAME
                         ● Theory / principle
                                  │

🔵 CONTEXT FIELD ●───────────────★───────────────● 🟢 PRIMARY ACTION
 Background facts       Synthesis       Recommendation

                                  │
                         🟡 ADJACENT IDEA
                         Useful but secondary

                                  ○
                         🔴 LOW-WEIGHT FRAME
                         Considered but weak
```

Transparency Notice:
Concept map only. No chain-of-thought, hidden reasoning, private deliberation, intermediate calculations, proprietary model state, or neural activations are displayed.
