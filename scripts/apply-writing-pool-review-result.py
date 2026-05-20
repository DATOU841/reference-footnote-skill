#!/usr/bin/env python3
"""Apply a writing-pool review result to the evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import WRITING_POOL_DECISIONS, ensure_task, print_json, read_json, result, update_flow_status, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--review-result", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    if not ledger_path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json missing"]))
        return 1
    review = read_json(args.review_result)
    if review.get("status") not in {"completed", "partial"}:
        print_json(result("failed", errors=["review result status must be completed or partial"]))
        return 1
    ledger = read_json(ledger_path)
    by_note = {entry.get("note_id"): entry for entry in ledger.get("entries", []) if entry.get("note_id")}
    errors = []
    for item in review.get("results", []):
        decision = item.get("decision")
        if decision not in WRITING_POOL_DECISIONS:
            errors.append(f"invalid decision for {item.get('insertion_id')}: {decision}")
            continue
        entry = by_note.get(item.get("insertion_id"))
        if not entry:
            errors.append(f"unknown insertion_id: {item.get('insertion_id')}")
            continue
        entry["writing_pool_decision"] = decision
        entry["writing_pool_fit"] = item.get("fit")
        entry["writing_pool_reason"] = item.get("reason")
        entry["writing_pool_risks"] = item.get("risks", [])
        if item.get("revised_note_text"):
            entry["writing_pool_revised_note_text"] = item.get("revised_note_text")
        if item.get("new_target_location"):
            entry["writing_pool_new_target_location"] = item.get("new_target_location")
        if item.get("rewritten_paragraph"):
            entry["writing_pool_rewritten_paragraph"] = item.get("rewritten_paragraph")
        if decision == "return_paragraph_for_rewrite":
            entry["final_decision"] = "blocked_rewrite_required"
        elif decision == "drop_note":
            entry["cleanup_status"] = "drop_requested"
    out = task / "state" / "evidence-trace-ledger.json"
    write_json(out, ledger)
    copy_path = task / "state" / "writing-pool-review-result.json"
    write_json(copy_path, review)
    update_flow_status(task, "S80", status="completed" if not errors else "failed", blocked=bool(errors), note="; ".join(errors) if errors else None)
    print_json(result("failed" if errors else "passed", output=str(out), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
