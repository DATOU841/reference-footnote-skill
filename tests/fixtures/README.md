# Fixtures

The fixture suite is fully offline. It uses a synthetic law article, synthetic RAG responses, and synthetic search-intake completion data.

Run:

```bash
python3 tests/run-fixtures.py --all
```

0.5.3-dev expects 62 fixtures. Fixtures 1-29 preserve legacy/offline compatibility through explicit pre-ingestion bypass where needed; fixtures 30-41 verify retrieval-first behavior; fixtures 42-58 cover Markdown grounding, evidence trace, writing-pool review, risk cleanup, full-text insertion, and final delivery; fixtures 59-62 cover the post-2.5 RAG executor, missing config blocker, executor response validation, and query-vs-ingestion boundary.
