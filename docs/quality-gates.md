# Quality Gates

Local gate:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

0.1.0-dev expects 15 offline fixtures to pass.

Release gate requires an approved Claude review and a clean git worktree with tag `0.1.0-dev`.
