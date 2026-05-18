# Collaboration Flow

`0.5.0-dev` uses a retrieval-first collaboration layer. ReferenceFootnote first derives article-level retrieval directions, then prepares an initial library-building package for `检索入库`. RAG reverse lookup happens only after structured ingestion completion and intake quality validation.

## Flow

1. Generate `search-blueprint.json` with `build-search-blueprint.py`.
2. Generate `search_intake_library_build` with `build-initial-search-handoff.py`.
3. Generate a skill call package with `build-search-intake-call.py`.
4. A user or outer orchestrator authorizes `检索入库` to execute the package.
5. `检索入库` returns `intake_completion` JSON with `library_build_summary`.
6. Record completion with `apply-intake-completion.py`.
7. Validate library quality with `validate-intake-quality.py`.
8. Build RAG reverse lookup request with `build-rag-request.py`.
9. Validate returned RAG response with `validate-rag-response.py`.
10. Build evidence map and, if needed, create round2 gap requests with `build-search-handoff.py`.
11. Generate footnote/reference plans, quality report, authenticity request, and delivery package.

`tests/run-fixtures.py` includes offline retrieval-first fixtures. They verify that RAG is blocked before ingestion, initial library handoff packages are produced, intake quality gates pass/fail deterministically, and delivery includes blueprint and intake gate artifacts.

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
- optional `allowed_server_entry_if_authorized`, which is metadata for `检索入库` and must not be executed by ReferenceFootnote
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
