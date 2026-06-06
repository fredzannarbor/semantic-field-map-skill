---
name: semantic-field-map
description: Prepend a compact Semantic Field Map to responses, showing the conceptual landscape behind an answer without revealing chain-of-thought or hidden reasoning. Use when the user wants responses to be more spatial, colorful, concept-aware, or explicitly asks for semantic field maps.
---

# Semantic Field Map

Before answering, prepend a compact Semantic Field Map unless the user disables it.

Do not reveal chain-of-thought, hidden reasoning, internal deliberations, or intermediate calculations. The map is an approximate semantic field: the concepts most relevant to the answer.

## Format

### Semantic Field Map

**Prompt Center:**  
[one-sentence summary]

**Conceptual Center of Gravity:**  
[dominant organizing idea]

```text
                     🟣 ABSTRACT FRAME
                            ●
                            │

🔵 CONTEXT FIELD ●──────★──────● 🟢 PRIMARY ACTION

                            │
                            ●
                    🟡 ADJACENT IDEA

                            ○
                    🔴 LOW-WEIGHT FRAME
```

Then answer the user normally.

## Rules

- Keep the map compact: usually 2 short fields plus the diagram.
- Use conceptual labels, not reasoning steps.
- Do not include private deliberation, scratch work, hidden calculations, or tool-only details.
- If the user asks for a terse answer, use a smaller map.
- If the user disables maps, answer normally without mentioning the skill.
