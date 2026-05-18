# Boundary Rules

Forbidden in 0.5.0-dev:

- CNKI, WoS, Zotero, PDF retrieval, or RAG ingestion.
- Live RAG reverse lookup.
- `openclaw-cnki-takeover`.
- `localhost:22` probing.
- writing-pool, advance-pool, mimo.
- production or staging deployment.
- formal article task execution.
- inventing references without a `检索入库` completion or user-declared existing RAG library.
- using ad hoc public web search results as formal academic references.
- marking unverified sources as `rag_verified`, `intake_completed`, or already ingested.

Allowed:

- Read and write files inside synthetic offline task directories.
- Generate structured handoff requests.
- Validate synthetic completion and RAG response fixtures.
- Install local runtime after review.

Allowed evidence provenance values for citation candidates are `rag_verified`, `intake_completed`, and `user_declared_existing`. Values such as `web_search`, `ai_generated`, `unverified`, or `fabricated` must remain outside final citation plans.
