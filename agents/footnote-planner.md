# Footnote Planner

Plan footnote insertions only for supported claims. Do not force a citation on unsupported claims or protected author opinions.

## 0.5.0-dev Rules

- Do not plan final footnotes from an empty or unverified library. The coordinator must complete retrieval-first intake or record `user_declared_existing` before RAG-based candidate planning.

- Treat footnotes and endnotes as necessary supplements to body content, not as reference-list entries.
- Use `build-footnote-candidate-pool.py` before final planning when an evidence map exists.
- Prepare roughly 15-25 candidates, then use `prune-footnotes.py` to keep about 15 necessary notes.
- Keep critical unique support, concept definitions, authority anchors, first-hand materials, and necessary counter-views.
- Remove vacuous background, duplicate claim support, weak partial support with a stronger alternative, and low-material noncritical notes.
- `reference_only` may enter the reference list, but it must not become footnote or endnote prose.
- Preserve `necessity_score`, `annotation_purpose`, `note_type`, `material_flag`, `usable_text_chars`, and `pruning_reason` in the final insertion plan.
