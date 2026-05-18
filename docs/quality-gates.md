# Quality Gates

Local gate:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

0.4.0-dev expects 29 offline fixtures to pass.

Release gate requires an approved Claude review and a clean git worktree with tag `0.4.0-dev`.

0.4.0-dev adds these citation-specific gates:

- Footnotes/endnotes must contain necessary supplemental content; `reference_only` entries cannot become footnote prose.
- Final footnote count should stay in the 10-20 range, with about 15 as the target.
- Final reference count should target 25-30; over 40 is blocking.
- Search-intake completion material pool should average at least 200 usable text chars per source pool; below that is a warning and must be surfaced.
- Authenticity verification results must cover every requested insertion before final consistency review.
