# Collaboration Flow

`0.2.0-dev` adds a collaboration layer for calling `检索入库` and then preparing post-ingestion RAG reverse lookup. The core rule is unchanged: ReferenceFootnote prepares structured packages; it does not execute real CNKI/WoS/Zotero/PDF/RAG work.

## Flow

1. Build evidence gaps with `build-evidence-map.py`.
2. Generate gap-driven search requests with `build-search-handoff.py`.
3. Generate a skill call package with `build-search-intake-call.py`.
4. A user or outer orchestrator authorizes `检索入库` to execute the package.
5. `检索入库` returns `intake_completion` JSON.
6. Record completion with `apply-intake-completion.py`.
7. Generate post-ingestion RAG call package with `build-post-ingestion-rag-call.py`.
8. A RAG platform operator returns `reverse_lookup_result`.
9. Validate returned RAG response with `validate-rag-response.py`.
10. Rebuild evidence map, footnote plan, quality report, and delivery package.

## Search-Intake Call Package

`build-search-intake-call.py` reads:

```text
state/search-intake-requests/<batch>.json
```

It writes:

```text
state/search-intake-calls/<batch>.json
state/search-intake-calls/<batch>.prompt.md
```

The JSON package contains:

- source and target skill names
- execution status `prepared_not_executed`
- explicit requirement for user authorization before real search
- the original `handoff.requests[]`
- expected `intake_completion` schema
- forbidden actions for ReferenceFootnote

The Markdown prompt is meant to be pasted into a new Codex turn that uses `检索入库`.

## Post-Ingestion RAG Call Package

`build-post-ingestion-rag-call.py` reads:

```text
state/intake-status.json
state/citation-needs.json
```

It writes:

```text
state/rag-calls/<batch>.json
```

Only completion rows whose `import_status.rag_indexed=true` become RAG lookup targets. This keeps the second lookup tied to confirmed ingestion, not to search promises.

## Boundary

ReferenceFootnote may say "call package prepared" but must not say search or RAG has completed until the responsible system returns a structured completion or response.

ReferenceFootnote must not:

- open CNKI or WoS
- save to Zotero
- fetch PDF
- import into RAG
- probe local SSH ports
- operate `openclaw-cnki-takeover`
- impersonate `检索入库` completion

## Failure Handling

If a call package is malformed, add a fixture and fix the generator. If `检索入库` returns partial or failed completion, ReferenceFootnote records it and keeps unresolved claims in the final human review list.
