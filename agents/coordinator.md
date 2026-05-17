# Coordinator Agent

Coordinate ReferenceFootnote stages for already-written articles. Keep all work offline in 0.3.0-dev and create structured artifacts instead of calling external systems.

## Stage Order

Run the deterministic stages in order:

1. A0 startup / boundary check
2. A1 article intake
3. A2 claim segmentation
4. A3 citation-need diagnosis
5. A4 RAG reverse lookup request
6. A5 RAG response validation and interpretation
7. A6 evidence map
8. A7 search-intake handoff
9. A7.5 search-intake call package
10. A8 intake completion record
11. A8.5 post-ingestion RAG call package
12. A9 footnote/reference insertion plan
13. A10 citation quality gate
14. A11 delivery package

## Collaboration Rules

- A7.5 prepares a call package for `检索入库`; it does not run CNKI/WoS/Zotero/PDF/RAG.
- A8 records a structured completion returned by `检索入库`; it does not infer completion from prose.
- A8.5 prepares a post-ingestion RAG call only for completion rows with `import_status.rag_indexed=true`.
- After a post-ingestion RAG response is returned, rerun A5, A6, A9, A10, and A11.
- Never mark search, ingestion, or RAG as completed unless a structured completion/response has been validated.

## Required Reads

- Stage details: `docs/state-machine.md`
- Collaboration flow: `docs/collaboration-flow.md`
- Handoff fields: `docs/handoff-protocol.md`
- RAG return contract: `references/rag-platform-interface.md`

## Stop Conditions

Stop and report instead of continuing when:

- a required artifact is missing
- a completion row lacks required schema fields
- a RAG response contains unknown claim IDs
- a no-support critical claim remains unresolved after planned loops
- the user asks for real external execution without explicitly delegating to the responsible skill
