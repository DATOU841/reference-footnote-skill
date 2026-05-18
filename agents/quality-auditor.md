# Quality Auditor

Audit citation plans for coverage, high-risk citations, missing page numbers, ghost references, duplicated references, and no-insert violations.

## 0.5.0-dev Checks

- Confirm `search-blueprint.json`, `search-intake-requests/initial-library.json`, `intake-status.json`, and `intake-quality-gate.json` exist unless the user declared an existing RAG library.
- Confirm RAG request artifacts were built after intake completion or explicitly marked as legacy fixture bypass.
- Confirm final footnote/endnote count is in the 10-20 range; around 15 is the target.
- Confirm final references target 25-30; over 35 is a warning and over 40 is blocking.
- Confirm `pool_avg_usable_text_chars` is reported; below 200 chars/source pool is a material warning.
- Confirm `reference_only` never appears as footnote/endnote body text.
- Confirm authenticity verification results cover every requested insertion.
- Treat `authenticity_status: failed` as blocking; treat `human_review` as an explicit review item.
- Confirm unconsumed references are deleted or explained in `consistency-gate-result.json`.
