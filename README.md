# ReferenceFootnote / 参考文献补注

`参考文献补注 / ReferenceFootnote` is a Codex skill for already-written academic articles. It analyzes citation needs, builds RAG reverse-lookup requests, interprets evidence, generates search-intake handoffs, plans footnote/reference insertions, and packages citation QA outputs.

Version: `0.1.0-dev`.

This version is offline-first. It must not run formal article tasks, CNKI/WoS/Zotero/PDF retrieval, RAG ingestion, writing-pool, advance-pool, mimo, server deployment, or production workflows.

Local gates:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

Publication stays blocked until Claude review exists and P0/P1 findings are fixed.
