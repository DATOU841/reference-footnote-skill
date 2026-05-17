# Boundary Rules

Forbidden in 0.2.0-dev:

- CNKI, WoS, Zotero, PDF retrieval, or RAG ingestion.
- Live RAG reverse lookup.
- `openclaw-cnki-takeover`.
- `localhost:22` probing.
- writing-pool, advance-pool, mimo.
- production or staging deployment.
- formal article task execution.

Allowed:

- Read and write files inside synthetic offline task directories.
- Generate structured handoff requests.
- Validate synthetic completion and RAG response fixtures.
- Install local runtime after review.
