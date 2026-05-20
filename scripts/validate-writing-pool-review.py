#!/usr/bin/env python3
"""Validate writing-pool review decisions before risk cleanup."""

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
    for entry in ledger.get("entries", []):
        decision = entry.get("writing_pool_decision")
        if not entry.get("note_id"):
            continue
        if not decision:
            warnings.append(f"{entry.get('note_id')} has no writing-pool review decision")
        if decision == "return_paragraph_for_rewrite" and not entry.get("writing_pool_rewritten_paragraph"):
            blocking.append(f"{entry.get('note_id')} requires full paragraph rewrite")
        if decision == "drop_note":
            warnings.append(f"{entry.get('note_id')} must enter risk cleanup as drop_note")
        if decision == "move_note" and not entry.get("writing_pool_new_target_location"):
            blocking.append(f"{entry.get('note_id')} move_note missing new_target_location")
        if entry.get("support_strength") == "analogy_only" and decision == "keep":
            warnings.append(f"{entry.get('note_id')} analogy_only kept; note wording must keep analogy boundary")
    report = {"status": "failed" if blocking else "passed", "blocking_issues": blocking, "warnings": warnings}
    out = task / "state" / "writing-pool-gate-result.json"
    write_json(out, report)
    print_json(result(report["status"] if report["status"] == "passed" or not args.allow_fail else "passed", output=str(out), report=report))
    return 0 if report["status"] == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
