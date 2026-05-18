#!/usr/bin/env python3
"""Apply a synthetic authenticity verification result."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import AUTHENTICITY_STATUSES, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    request_path = task / "state" / "authenticity-verification-request.json"
    if not request_path.exists():
        print_json(result("failed", errors=["authenticity-verification-request.json missing"]))
        return 1
    request = read_json(request_path)
    verification = read_json(args.verification)
    errors = []
    issues = []
    req_ids = {item["insertion_id"] for item in request.get("items", [])}
    seen = set()
    for item in verification.get("results", []):
        ins_id = item.get("insertion_id")
        seen.add(ins_id)
        status = item.get("authenticity_status")
        if ins_id not in req_ids:
            errors.append(f"unexpected insertion_id: {ins_id}")
        if status not in AUTHENTICITY_STATUSES:
            errors.append(f"invalid authenticity_status for {ins_id}: {status}")
        if status != "verified" or item.get("risks"):
            issues.append({
                "insertion_id": ins_id,
                "authenticity_status": status,
                "risks": item.get("risks", []),
                "resolution_required": item.get("resolution_required", "manual_review"),
            })
    missing = sorted(req_ids - seen)
    if missing:
        errors.append(f"missing verification results: {', '.join(missing)}")
    out_data = {
        "status": "failed" if errors else verification.get("status", "completed"),
        "batch_id": verification.get("batch_id"),
        "results": verification.get("results", []),
        "issues": issues,
        "errors": errors,
    }
    out = task / "state" / "authenticity-verification-result.json"
    write_json(out, out_data)
    write_json(task / "state" / "authenticity-issues.json", {"issues": issues, "errors": errors})
    print_json(result("failed" if errors else "passed", output=str(out), issues=len(issues), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
