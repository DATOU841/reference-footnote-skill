#!/usr/bin/env python3
"""Apply a synthetic search-intake completion payload."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


REQUIRED_RESULT_FIELDS = {"request_id", "claim_id", "status", "sources_found", "kb_routing", "pdf_status", "import_status"}
VALID_RESULT_STATUSES = {"completed", "partial", "failed", "ingested"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--completion", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    completion = read_json(args.completion)
    errors = []
    if completion.get("status") not in {"completed", "partial", "failed"}:
        errors.append("completion status must be completed, partial, or failed")
    if not completion.get("handoff_id"):
        errors.append("handoff_id missing")
    for idx, item in enumerate(completion.get("results", []), start=1):
        missing = sorted(REQUIRED_RESULT_FIELDS - set(item))
        if missing:
            errors.append(f"results[{idx}] missing fields: {', '.join(missing)}")
        if item.get("status") not in VALID_RESULT_STATUSES:
            errors.append(f"results[{idx}] invalid status: {item.get('status')}")
        if not isinstance(item.get("sources_found", []), list):
            errors.append(f"results[{idx}].sources_found must be a list")
    out = task / "state" / "intake-status.json"
    write_json(out, completion)
    print_json(result("failed" if errors else "passed", output=str(out), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
