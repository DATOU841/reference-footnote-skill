# State Machine

ReferenceFootnote 0.5.3-dev uses a single-line stage machine. The main status source is `state/referencefootnote-flow-status.json`; the main evidence source is `state/evidence-trace-ledger.json`.

| Stage | Name | Main Output | Gate |
| --- | --- | --- | --- |
| S00 | startup | `referencefootnote-flow-status.json` | boundary checks pass |
| S10 | article intake | `article-structure.json` | sections and paragraphs exist |
| S20 | claim/citation diagnosis | `claim-segments.json`, `citation-needs.json` | non-trivial claims classified |
| S30 | search blueprint | `search-blueprint.json` | retrieval directions present |
| S40 | intake handoff | `search-intake-requests/*.json`, `search-intake-calls/*.json` | call package prepared, not executed |
| S45 | intake completion/gate | `intake-status.json`, `intake-quality-gate.json` | source pool quality checked |
| S50a | build RAG request | `rag-requests/*.json` | post-2.5 request exists |
| S50b | execute RAG reverse lookup | `rag-calls/*.response.json` | executor response exists or `missing_rag_executor_config` blocks |
| S50c | validate RAG response | `evidence-interpretations/*.json` | per-claim RAG response interpreted |
| S55 | grounding resolution | `grounding-resolution.json` | Markdown/parsed text/page-map/PDF fallback state resolved |
| S60 | evidence trace ledger | `evidence-trace-ledger.json` | full-text order trace built |
| S65 | evidence map/gap handoff | `evidence-map.json`, gap requests | unsupported needs routed |
| S70 | note/reference planning | `insertion-plan.json` | no forced notes for unsupported claims |
| S80 | writing-pool review | `writing-pool-review-request/result.json` | note position and wording reviewed independently |
| S85 | risk inventory | `risk-inventory.json` | blocking and warning risks classified |
| S90 | risk cleanup | `risk-cleanup-plan/result.json` | blocking risks resolved or explicitly blocked |
| S95 | cleaned rebuild | `cleaned-citation-needs.json`, `cleaned-insertion-plan.json`, `cleaned-reference-list.json` | deleted notes and unconsumed refs removed |
| S100 | full-text insertion | `full-text-with-notes.md` | complete text exists |
| S105 | full-order audit | `full-order-audit.json`, `.md` | every note follows full-text order |
| S110 | final delivery gate | `final-gate-result.json` | ledger, cleanup, audit, full text all pass |
| S120 | delivery package | `delivery/` | top-level package is not cluttered |

Collaboration stages generate search-intake call packages, but post-2.5 RAG reverse lookup is a ReferenceFootnote responsibility. The skill does not run real CNKI/WoS/Zotero/PDF acquisition/RAG import. Writing-pool review is independent of the `正文写作` skill and cannot generate an article from scratch.
