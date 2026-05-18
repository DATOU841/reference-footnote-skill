# State Machine

ReferenceFootnote uses an offline-first stage machine:

| Stage | Name | Input | Output | Gate |
| --- | --- | --- | --- | --- |
| A0 | startup | repository/config | `state/status.json` | boundary checks pass |
| A1 | article intake | article file | `article-structure.json` | sections and paragraphs exist |
| A2 | claim segmentation | article structure | `claim-segments.json` | claims generated for paragraphs |
| A3 | citation diagnosis | claim segments | `citation-needs.json` | non-trivial claims classified |
| A3.5 | search blueprint | article + citation needs | `search-blueprint.json` | retrieval directions and library quality floor present |
| A4 | initial library handoff | search blueprint | `search-intake-requests/initial-library.json` | `request_type=search_intake_library_build` |
| A4.5 | initial library skill call | initial handoff | `search-intake-calls/initial-library.json` and `.prompt.md` | call package prepared, not executed |
| A5 | intake completion | completion response | `intake-status.json` | completion status and usable text metrics recorded |
| A5.5 | intake quality gate | intake status + blueprint | `intake-quality-gate.json` | pool size, text, type coverage, RAG index ratio checked |
| A6 | RAG request build | citation needs + intake status | `rag-requests/*.json` | blocked unless initial library exists or user declared existing RAG |
| A6.5 | RAG response interpretation | request + response | `evidence-interpretations/*.json` | support/risk labels present |
| A7 | evidence map | citation needs + interpretations | `evidence-map.json` | coverage summary complete |
| A7.5 | gap search-intake handoff | evidence map | `search-intake-requests/gap-round2.json` | unsupported critical/important claims converted for round2 |
| A7.6 | gap search-intake skill call | gap request | `search-intake-calls/gap-round2.json` and `.prompt.md` | call package prepared, not executed |
| A8 | round2 intake completion | completion response | `intake-status-round2.json` | optional second-round completion |
| A8.5 | post-ingestion RAG call | intake completion + citation needs | `rag-calls/*.json` | RAG call package prepared for indexed sources |
| A9a | footnote candidate pool | evidence map + intake status | `footnote-candidate-pool.json` | 15-25 candidates prepared where available |
| A9b | footnote necessity pruning | candidate pool | `footnote-pruning-result.json` | empty, repetitive, background-only, and invalid candidates removed |
| A9c | reference candidate pruning | candidate pool + kept footnotes | `reference-pruning-plan.json` | 25-30 important references targeted |
| A9 | footnote plan | pruning results + evidence map | `insertion-plan.json` | no forced citation on unsupported claims |
| A10 | citation quality gate | insertion plan | `quality-report.json` | blocking issues identified |
| A10a | authenticity request | insertion plan | `authenticity-verification-request.json` | PDF + RAG check package prepared, not executed |
| A10b | authenticity result | external/synthetic verification result | `authenticity-verification-result.json` | result schema and issue list validated |
| A10c | consistency gate | insertion plan + verification result | `consistency-gate-result.json` | note/reference boundaries checked |
| A11 | delivery package | all prior outputs | `delivery/` | required artifacts copied |

Stages are deterministic in 0.5.0-dev. Collaboration and verification stages produce call packages or consume offline回执 only; they do not execute real search, ingestion, PDF checks, or RAG queries. RAG reverse lookup is retrieval-first: it is blocked until an initial library completion exists, unless the user explicitly declared an existing RAG library.
