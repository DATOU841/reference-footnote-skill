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
    "A9": "state/insertion-plan.json",
    "A10": "state/quality-report.json",
    "A11": "delivery/summary.md",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_FILES))
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    missing = [rel for stage, rel in STAGE_FILES.items() if stage <= args.stage and not (task / rel).exists()]
    data = result("failed" if missing else "passed", stage=args.stage, missing=missing)
    print_json(data)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
