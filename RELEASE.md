# Release Notes

## 0.2.0-dev

Status: pre-Claude-review development build.

### Scope

- Offline collaboration call package for `检索入库`.
- Offline post-ingestion RAG reverse-lookup call package.
- Explicit boundary that ReferenceFootnote prepares calls but never executes real CNKI/WoS/Zotero/PDF/RAG work.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, tag `0.2.0-dev`, and push.

## 0.1.0-dev

Status: pre-Claude-review development build.

### Scope

- Offline stage machine and protocol implementation.
- Fixture-driven RAG reverse lookup, evidence interpretation, search-intake handoff, footnote planning, and delivery package generation.
- Local runtime install support after review.
- Public Chinese introduction for demonstration and stakeholder-facing feature overview.
- Expanded handoff compatibility with `检索入库` and `正文写作`, including round, gap, KB routing, evidence type, source role, consumption depth, and GB/T 7714 footnote fields.

### Planned For 0.2.0

- Multi-round RAG reverse lookup closure.
- Existing-reference merge with Zotero reference master.
- Source concentration report and source consumption priority map generation.
- Writer scan output conversion for citation hygiene and critical claim checks.
- GitHub release gate script for staging/production promotion.

### Blocked

- No production deployment.
- No staging deployment.
- No real RAG query, RAG ingestion, CNKI/WoS/Zotero/PDF retrieval, writing-pool, advance-pool, or mimo.
- No formal article task execution.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, and tag `0.1.0-dev`.
