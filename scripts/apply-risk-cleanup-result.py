#!/usr/bin/env python3
"""Apply a risk cleanup result to the evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--cleanup-result", type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    plan_path = task / "state" / "risk-cleanup-plan.json"
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    if not ledger_path.exists() or not plan_path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json or risk-cleanup-plan.json missing"]))
        return 1
    ledger = read_json(ledger_path)
    if args.cleanup_result:
        cleanup = read_json(args.cleanup_result)
    else:
        plan = read_json(plan_path)
        cleanup = {
            "cleanup_id": plan.get("cleanup_id", "cleanup-001"),
            "actions_applied": [
                {**action, "result": "blocked_pending_human" if action.get("requires_human_confirmation") else "applied"}
                for action in plan.get("actions", [])
            ],
        }
    by_note = {entry.get("note_id"): entry for entry in ledger.get("entries", []) if entry.get("note_id")}
    by_claim = {entry.get("claim_id"): entry for entry in ledger.get("entries", [])}
    still_blocking = []
    for action in cleanup.get("actions_applied", []):
        entry = by_note.get(action.get("note_id")) or by_claim.get(action.get("claim_id"))
        if not entry:
            continue
        act = action.get("action")
        if action.get("result") == "blocked_pending_human" or act == "block_until_full_paragraph":
            entry["cleanup_status"] = "blocked_pending_human"
            entry["final_decision"] = "blocked_rewrite_required"
            still_blocking.append(action)
            continue
        if act in {"delete_note", "delete_reference"}:
            entry["cleanup_status"] = "resolved"
            entry["final_decision"] = "deleted_by_cleanup"
        elif act in {"downgrade_note", "downgrade_to_analogy_only", "revise_note_with_boundary", "mark_page_pending", "mark_ocr_uncertain"}:
            entry["cleanup_status"] = "resolved"
            entry["final_decision"] = "downgraded_by_cleanup"
            flags = set(entry.get("risk_flags", []))
            if act in {"downgrade_note", "downgrade_to_analogy_only"}:
                entry["support_strength"] = "analogy_only"
                flags.add("direct_experiment_missing")
            entry["risk_flags"] = sorted(flags)
        else:
            entry["cleanup_status"] = "human_review"
            entry["final_decision"] = "needs_human_review"
    cleanup["total_resolved"] = sum(1 for a in cleanup.get("actions_applied", []) if a.get("result") == "applied")
    cleanup["total_remaining"] = len(still_blocking)
    cleanup["still_blocking"] = still_blocking
    write_json(ledger_path, ledger)
    out = task / "state" / "risk-cleanup-result.json"
    write_json(out, cleanup)
    update_flow_status(task, "S90", blocked=bool(still_blocking), note=f"still blocking={len(still_blocking)}")
    print_json(result("passed" if not still_blocking else "failed", output=str(out), still_blocking=len(still_blocking)))
    return 1 if still_blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
