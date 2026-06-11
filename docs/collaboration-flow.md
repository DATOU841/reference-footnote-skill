# Collaboration Flow

`0.5.3-dev` uses a retrieval-first collaboration layer. ReferenceFootnote first derives article-level retrieval directions, then prepares an initial library-building package for `检索入库`. RAG reverse lookup happens only after structured ingestion completion and intake quality validation, and is then executed by ReferenceFootnote's own RAG executor.

## Flow

1. Generate `search-blueprint.json` with `build-search-blueprint.py`.
2. Generate `search_intake_library_build` with `build-initial-search-handoff.py`.
3. Generate a skill call package with `build-search-intake-call.py`.
4. A user or outer orchestrator authorizes `检索入库` to execute the package.
5. `检索入库` returns `intake_completion` JSON with `library_build_summary`.
6. Record completion with `apply-intake-completion.py`.
7. Validate library quality with `validate-intake-quality.py`.
8. Build RAG reverse lookup request with `build-rag-request.py`.
9. Execute read-only RAG reverse lookup with `run-rag-reverse-lookup.py`; the internal response is `state/rag-calls/<batch>.response.json`.
10. Validate the executor response with `validate-rag-response.py`.
11. Resolve Markdown/page-map grounding with `resolve-grounding.py`.
12. Build evidence map and, if needed, create round2 gap requests with `build-search-handoff.py`.
13. Generate footnote/reference plans, quality report, authenticity request, and delivery package.

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

Only completion rows whose `import_status.rag_indexed=true` become RAG lookup targets. This keeps the second lookup tied to confirmed ingestion, not to search promises. The package is executed by `run-rag-reverse-lookup.py`; it is not a user-facing回执 request.

## Boundary

ReferenceFootnote may say "search-intake call package prepared" but must not say search or ingestion has completed until `检索入库` returns structured completion. For RAG reverse lookup, ReferenceFootnote writes and consumes its own executor response. If executor configuration is missing, stop with `missing_rag_executor_config`; do not ask the user to supply a response. If ingestion already produced MinerU/MU Markdown or equivalent parsed text, use it as the default verification artifact; request PDF fallback only for page-map, OCR, or layout risks.

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
