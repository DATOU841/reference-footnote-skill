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

## Writer Evidence Type Mapping

ReferenceFootnote also carries evidence types for `正文写作` consumption:

| ReferenceFootnote context | Writer evidence type | Use |
| --- | --- | --- |
| theoretical or academic judgment supported by secondary literature | `后设归纳` | academic positioning, theory background |
| textual or doctrinal analysis | `文本证据` | concept comparison, textual support |
| empirical, data, case, statute, archival, or original source material | `经验材料` / `一手材料` | factual or institutional claims |
| direct teacher-student, correspondence, or transmission record | `师承证据` | transmission or influence claims |

Evidence type affects insertion planning:

- `strong_support` + precise page + suitable evidence type can become a direct insertion.
- `partial_support` or approximate evidence type must set `requires_rewrite=true`.
- `background_only` may become background citation but cannot support a concrete claim.
- `conflict` must never become support; it may become opposing-view material.

The type is passed through `insertion_plan.insertions[].evidence_type` and `handoff_to_writing.json` so writer-side argument-strength governance can lower, delete, or re-route claims when evidence is insufficient.
