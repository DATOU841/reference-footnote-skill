# Coordinator Agent

Coordinate ReferenceFootnote stages for already-written articles. Keep all work offline in 0.5.0-dev and create structured artifacts instead of calling external systems.

## Stage Order

Run the deterministic stages in order:

1. A0 startup / boundary check
2. A1 article intake
3. A2 claim segmentation
4. A3 citation-need diagnosis
5. A3.5 search blueprint
6. A4 initial library-building handoff
7. A4.5 initial search-intake call package
8. A5 intake completion record
9. A5.5 intake quality gate
10. A6 RAG reverse lookup request
11. A6.5 RAG response validation and interpretation
12. A7 evidence map
13. A7.5 round2 gap handoff
14. A7.6 round2 gap call package
15. A8/A8.5 optional round2 completion and RAG call
16. A9a-A9c footnote/reference candidate and pruning stages
17. A9-A11 plan, quality, authenticity, consistency, and delivery

## Collaboration Rules

- A3.5 must derive retrieval directions from the whole article before any reference selection.
- A4/A4.5 prepare an initial `search_intake_library_build` package for `检索入库`; ReferenceFootnote does not run CNKI/WoS/Zotero/PDF/RAG.
- A5 records a structured completion returned by `检索入库`; it does not infer completion from prose.
- A5.5 must validate pool size, usable text, source type coverage, and RAG indexing before A6.
- A6 RAG reverse lookup is blocked unless A5 is complete or the user declared an existing RAG library.
- A8.5 prepares a post-ingestion RAG call only for completion rows with `import_status.rag_indexed=true`.
- After a post-ingestion RAG response is returned, rerun A5, A6, A9a, A9b, A9c, A9, A10, and A11.
- A9a prepares footnote candidates only where the evidence map has a usable candidate; unsupported claims remain no-insert or gap handoff items.
- A9b keeps footnotes as necessary content supplements, not bibliographic filler. Remove empty background, duplicate, low-necessity, and weak-material candidates unless they are the only critical support.
- A9c keeps the most important consumed references and explains or removes unconsumed references.
- A10a only prepares a PDF + RAG authenticity request; it does not fetch PDFs or run RAG.
- A10b only applies a structured verification result returned by an external operator or fixture.
- A10c must reject `reference_only` content in footnote/endnote prose and surface failed authenticity checks.
- Never mark search, ingestion, or RAG as completed unless a structured completion/response has been validated.
- Never treat `reference_only` as footnote body text.

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
- a footnote/endnote insertion has no supplemental text
- a `reference_only` item is about to enter footnote/endnote prose
- an authenticity result is missing for a requested insertion
- a no-support critical claim remains unresolved after planned loops
- the user asks for real external execution without explicitly delegating to the responsible skill
