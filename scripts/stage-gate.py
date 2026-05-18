#!/usr/bin/env python3
"""Check stage gate artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, result

STAGE_FILES = {
    "A0": "state/status.json",
    "A1": "state/article-structure.json",
    "A2": "state/claim-segments.json",
    "A3": "state/citation-needs.json",
    "A4": "state/rag-requests/batch-01.json",
    "A5": "state/evidence-interpretations/batch-01.json",
    "A6": "state/evidence-map.json",
    "A7": "state/search-intake-requests/batch-01.json",
    "A8": "state/intake-status.json",
    "A9a": "state/footnote-candidate-pool.json",
    "A9b": "state/footnote-pruning-result.json",
    "A9c": "state/reference-pruning-plan.json",
    "A9": "state/insertion-plan.json",
    "A10": "state/quality-report.json",
    "A10a": "state/authenticity-verification-request.json",
    "A10b": "state/authenticity-verification-result.json",
    "A10c": "state/consistency-gate-result.json",
    "A11": "delivery/summary.md",
}


STAGE_ORDER = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9a", "A9b", "A9c", "A9", "A10", "A10a", "A10b", "A10c", "A11"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=STAGE_ORDER)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    target_stage = STAGE_ORDER.index(args.stage)
    missing = [STAGE_FILES[stage] for stage in STAGE_ORDER[:target_stage + 1] if not (task / STAGE_FILES[stage]).exists()]
    data = result("failed" if missing else "passed", stage=args.stage, missing=missing)
    print_json(data)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
