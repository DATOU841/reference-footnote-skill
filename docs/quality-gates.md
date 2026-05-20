# Quality Gates

Local gate:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

0.5.2-dev expects 58 offline fixtures to pass.

Release gate requires an approved Claude review and a clean git worktree with tag matching `VERSION`.

Blocking rules:

- Footnotes/endnotes must contain necessary supplemental content; `reference_only` entries cannot become footnote prose.
- `analogy_only` cannot be counted as direct support and cannot be final-inserted as if it were `strong_support`.
- `ownership_unverified` cannot be final-inserted as verified fact.
- Risk inventory must be followed by risk cleanup and cleaned artifact rebuild before final delivery.
- The final package must include `evidence-trace-ledger.json`, `full-order-audit.json`, `risk-inventory.json`, `risk-cleanup-result.json`, and `full-text-with-notes.md`.
- Writing-pool decisions of `return_paragraph_for_rewrite` block final delivery until a complete paragraph is returned and accepted.
- Unconsumed references are blocking in risk cleanup unless explicitly moved out of the final reference list.
- Grounding gates remain explicit: `strong_support` with unresolved grounding blocks; chunk-only support warns; PDF fallback blocks until reviewed or downgraded.
- Final delivery must put process materials under `delivery/process/`; top-level files are reserved for the main text, audit, risk residue, ledger, final gate, summary, and statistics.
