# Evidence Classification

Support strengths:

| Strength | Meaning | Citation Use |
| --- | --- | --- |
| `strong_support` | directly supports the claim | usable if no blocking risk |
| `partial_support` | supports part of the claim | requires limitation or rewrite |
| `background_only` | provides context only | background citation only |
| `conflict` | contradicts the claim | not support; may become opposing view |
| `no_support` | no candidate support found | create gap handoff or human review |

Risk flags:

- `page_missing`: page number is absent.
- `ocr_uncertain`: snippet text needs source verification.
- `secondhand_citation`: candidate may cite another source.
- `concept_approximate`: concept match is close but not exact.
- `temporal_mismatch`: source timing does not match claim scope.
- `discipline_cross`: source is from another discipline.
- `translation_gap`: translated concept may not align.

Unsupported critical claims must not receive fabricated notes.
