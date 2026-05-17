# State Machine

ReferenceFootnote uses an offline-first stage machine:

| Stage | Name | Input | Output | Gate |
| --- | --- | --- | --- | --- |
| A0 | startup | repository/config | `state/status.json` | boundary checks pass |
| A1 | article intake | article file | `article-structure.json` | sections and paragraphs exist |
| A2 | claim segmentation | article structure | `claim-segments.json` | claims generated for paragraphs |
| A3 | citation diagnosis | claim segments | `citation-needs.json` | non-trivial claims classified |
| A4 | RAG request build | citation needs | `rag-requests/*.json` | request schema valid |
| A5 | RAG response interpretation | request + response | `evidence-interpretations/*.json` | support/risk labels present |
| A6 | evidence map | citation needs + interpretations | `evidence-map.json` | coverage summary complete |
| A7 | search-intake handoff | evidence map | `search-intake-requests/*.json` | unsupported critical/important claims converted |
| A7.5 | search-intake skill call | search-intake request | `search-intake-calls/*.json` and `.prompt.md` | call package prepared, not executed |
| A8 | intake completion | completion response | `intake-status.json` | completion status recorded |
| A8.5 | post-ingestion RAG call | intake completion + citation needs | `rag-calls/*.json` | RAG call package prepared for indexed sources |
| A9 | footnote plan | evidence map + article | `insertion-plan.json` | no forced citation on unsupported claims |
| A10 | citation quality gate | insertion plan | `quality-report.json` | blocking issues identified |
| A11 | delivery package | all prior outputs | `delivery/` | required artifacts copied |

Stages are deterministic in 0.2.0-dev. Collaboration stages produce call packages only; they do not execute real search, ingestion, or RAG queries. Failures must be captured as offline fixtures before script or skill changes.
