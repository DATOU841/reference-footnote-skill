# Quality Gates

Local gate:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

0.5.1-dev expects 51 offline fixtures to pass.

Release gate requires an approved Claude review and a clean git worktree with tag `0.5.1-dev`.

0.5.1-dev keeps the 0.5 retrieval-first gates and adds Markdown-first grounding gates:

- Footnotes/endnotes must contain necessary supplemental content; `reference_only` entries cannot become footnote prose.
- Final footnote count should stay in the 10-20 range, with about 15 as the target.
- Final reference count should target 25-30; over 40 is blocking.
- Search-intake completion material pool should average at least 200 usable text chars per source pool; below that is a warning and must be surfaced.
- Authenticity verification results must cover every requested insertion before final consistency review.
- Retrieval-first gates are blocking: `search-blueprint.json`, `search-intake-requests/initial-library.json`, and `intake-status.json` must exist before citation planning unless the user declared an existing RAG library.
- A5.5 intake quality gate checks initial pool size, pool average usable text, source type coverage, and RAG indexed ratio.
- Grounding gates are explicit: `strong_support` with `unresolved_grounding` blocks; `strong_support` with `chunk_only_grounding` warns; `pdf_fallback_required` blocks until fallback verification or human review is recorded.
- `analogy_only` is never counted as direct support and should not produce automatic footnote insertion.
