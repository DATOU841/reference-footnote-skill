#!/usr/bin/env python3
"""Rebuild cleaned citation needs, insertion plan, and references after risk cleanup."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    plan_path = task / "state" / "insertion-plan.json"
    needs_path = task / "state" / "citation-needs.json"
    cleanup_path = task / "state" / "risk-cleanup-result.json"
    missing = [str(p.name) for p in [ledger_path, plan_path, needs_path, cleanup_path] if not p.exists()]
    if missing:
        print_json(result("failed", errors=[f"missing: {', '.join(missing)}"]))
        return 1
    ledger = read_json(ledger_path)
    plan = read_json(plan_path)
    needs = read_json(needs_path)
    deleted_notes = {e.get("note_id") for e in ledger.get("entries", []) if e.get("final_decision") == "deleted_by_cleanup"}
    blocked = [e for e in ledger.get("entries", []) if e.get("final_decision") == "blocked_rewrite_required"]
    kept_insertions = [ins for ins in plan.get("insertions", []) if ins.get("insertion_id") not in deleted_notes]
    consumed_refs = {ins.get("evidence_basis", {}).get("source_ref_id") for ins in kept_insertions if ins.get("evidence_basis", {}).get("source_ref_id")}
    kept_refs = [ref for ref in plan.get("reference_list", {}).get("new_references", []) if ref.get("ref_id") in consumed_refs]
    cleaned_needs = {
        **needs,
        "cleaned_after_risk_cleanup": True,
        "needs": [
            {**need, "cleanup_status": next((e.get("cleanup_status") for e in ledger.get("entries", []) if e.get("claim_id") == need.get("claim_id")), None)}
            for need in needs.get("needs", [])
        ],
    }
    cleaned_plan = {
        **plan,
        "insertions": kept_insertions,
        "reference_list": {**plan.get("reference_list", {}), "new_references": kept_refs, "cleaned_after_risk_cleanup": True},
        "risk_cleanup_applied": True,
    }
    gap_needs = [e for e in ledger.get("entries", []) if e.get("final_decision") in {"needs_gap_handoff", "deleted_by_cleanup"} and e.get("citation_need") in {"critical", "important"}]
    human_review = [e for e in ledger.get("entries", []) if e.get("final_decision") in {"needs_human_review", "blocked_rewrite_required"}]
    write_json(task / "state" / "cleaned-citation-needs.json", cleaned_needs)
    write_json(task / "state" / "cleaned-insertion-plan.json", cleaned_plan)
    write_json(task / "state" / "cleaned-reference-list.json", {"references": kept_refs})
    write_json(task / "state" / "cleaned-补库-needs.json", {"needs": gap_needs})
    write_json(task / "state" / "still-needs-human-review.json", {"items": human_review})
    update_flow_status(task, "S95", blocked=bool(blocked), note=f"cleaned insertions={len(kept_insertions)} refs={len(kept_refs)}")
    print_json(result("passed" if not blocked else "failed", cleaned_insertions=len(kept_insertions), cleaned_references=len(kept_refs), human_review=len(human_review)))
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
