#!/usr/bin/env python3
"""Check ReferenceFootnote stage gate artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, result
from wenheng_native import add_wenheng_args, verify_wenheng_native

STAGE_FILES = {
    "S00": "state/referencefootnote-flow-status.json",
    "S10": "state/article-structure.json",
    "S20": "state/citation-needs.json",
    "S30": "state/search-blueprint.json",
    "S40": "state/search-intake-calls/initial-library.json",
    "S45": "state/intake-quality-gate.json",
    "S50": ["state/rag-calls/batch-01.response.json", "state/evidence-interpretations/batch-01.json"],
    "S55": "state/grounding-resolution.json",
    "S60": "state/evidence-trace-ledger.json",
    "S65": "state/evidence-map.json",
    "S70": "state/insertion-plan.json",
    "S80": "state/writing-pool-review-request.json",
    "S85": "state/risk-inventory.json",
    "S90": "state/risk-cleanup-result.json",
    "S95": "state/cleaned-insertion-plan.json",
    "S100": "state/full-text-with-notes.md",
    "S105": "state/full-order-audit.json",
    "S110": "state/final-gate-result.json",
    "S120": "delivery/summary.md",
}

STAGE_ORDER = list(STAGE_FILES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=STAGE_ORDER)
    add_wenheng_args(parser)
    args = parser.parse_args()
    wenheng_binding = verify_wenheng_native(args, skill_id="reference_footnote", task_type="reference_footnote", writing=True)
    task = ensure_task(args.task_dir)
    target_stage = STAGE_ORDER.index(args.stage)
    missing = []
    for stage in STAGE_ORDER[:target_stage + 1]:
        required = STAGE_FILES[stage]
        paths = required if isinstance(required, list) else [required]
        missing.extend(path for path in paths if not (task / path).exists())
    data = result("failed" if missing else "passed", stage=args.stage, missing=missing, wenheng_native_binding=wenheng_binding)
    print_json(data)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
