# Fixtures

The fixture suite is fully offline. It uses a synthetic law article, synthetic RAG responses, and synthetic search-intake completion data.

Run:

```bash
python3 tests/run-fixtures.py --all
```

0.5.0-dev expects 41 fixtures. Fixtures 1-29 preserve legacy/offline compatibility through explicit pre-ingestion bypass where needed; fixtures 30-41 verify retrieval-first behavior, including RAG blocking before intake, search blueprint generation, initial library handoff, intake quality pass/fail, round2 gap handoff, and delivery propagation.
