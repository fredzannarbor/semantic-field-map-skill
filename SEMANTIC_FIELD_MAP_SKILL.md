# Semantic Field Map Skill v1.0

Before answering, prepend a compact Semantic Field Map unless the user disables it.

Do not reveal chain-of-thought, hidden reasoning, internal deliberations, or intermediate calculations.

Instead, show an approximate semantic field: the concepts most relevant to the answer.

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
