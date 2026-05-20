#!/usr/bin/env python3
"""Validate the full-order evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    path = task / "state" / "evidence-trace-ledger.json"
    if not path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json missing"]))
        return 1
    ledger = read_json(path)
    blocking = []
    warnings = []
    orders = [e.get("order") for e in ledger.get("entries", [])]
    if orders != sorted(orders):
        blocking.append("ledger entries are not in full-text order")
    seen = set()
    for entry in ledger.get("entries", []):
        key = entry.get("claim_id")
        if key in seen:
            blocking.append(f"duplicate claim_id in ledger: {key}")
        seen.add(key)
        if entry.get("note_id") and not entry.get("reference_id"):
            warnings.append(f"{entry.get('note_id')} has note but no reference_id")
        if entry.get("support_strength") == "analogy_only" and entry.get("final_decision") == "inserted":
            blocking.append(f"{entry.get('claim_id')} analogy_only cannot be direct inserted")
        if "ownership_unverified" in entry.get("risk_flags", []) and entry.get("final_decision") == "inserted":
            blocking.append(f"{entry.get('claim_id')} ownership_unverified cannot be final inserted without cleanup")
    report = {"status": "failed" if blocking else "passed", "blocking_issues": blocking, "warnings": warnings}
    out = task / "state" / "evidence-trace-ledger-gate.json"
    write_json(out, report)
    print_json(result(report["status"] if report["status"] == "passed" or not args.allow_fail else "passed", output=str(out), report=report))
    return 0 if report["status"] == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
