# Release Notes

## 0.5.1-dev

Status: pre-Claude-review development build.

### Scope

- Markdown-first grounding between RAG chunks, MinerU/MU Markdown or parsed text, page maps, and PDF fallback.
- `analogy_only` evidence classification for neighboring grid or adjacent-method literature.
- Grounding-aware evidence maps, insertion plans, quality reports, authenticity requests, and delivery handoffs.
- 51 offline fixtures covering retrieval-first and grounding behavior.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, tag `0.5.1-dev`, and push.

## 0.5.0-dev

Status: pre-Claude-review development build.

### Scope

- Retrieval-first stage machine and hard gates.
- Article-level search blueprint before any RAG reverse lookup.
- Initial `检索入库` library-build handoff and call package.
- Intake quality gate for pool size, usable text, type coverage, and RAG indexing.
- 41 offline fixtures covering legacy compatibility and retrieval-first behavior.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, tag `0.5.0-dev`, and push.

## 0.4.0-dev

Status: pre-Claude-review development build.

### Scope

- Footnote candidate pool, necessity pruning, and reference pruning.
- Search-intake material quality fields and pool-average warning gate.
- Offline authenticity verification request/result protocol for PDF + RAG dual checks.
- Footnote/endnote/reference-only boundary validation.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, tag `0.4.0-dev`, and push.

## 0.3.0-dev

Status: pre-Claude-review development build.

### Scope

- Offline post-ingestion RAG closure fixture.
- Expanded A7.5/A8.5 agent guidance.
- Documented collaboration call package schemas.

### Required Before Publication

Run local gates, request Claude review, fix P0/P1, commit, tag `0.3.0-dev`, and push.

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

### Planned After 0.2.0

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
