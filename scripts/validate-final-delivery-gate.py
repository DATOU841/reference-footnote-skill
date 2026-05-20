#!/usr/bin/env python3
"""Validate final ReferenceFootnote delivery readiness."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


REQUIRED = [
    "evidence-trace-ledger.json",
    "full-order-audit.json",
    "risk-inventory.json",
    "risk-cleanup-result.json",
    "cleaned-citation-needs.json",
    "cleaned-insertion-plan.json",
    "full-text-with-notes.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    missing = [name for name in REQUIRED if not (task / "state" / name).exists()]
    blocking = [f"missing {name}" for name in missing]
    warnings = []
    if (task / "state" / "risk-inventory.json").exists():
        inv = read_json(task / "state" / "risk-inventory.json")
        cleanup = read_json(task / "state" / "risk-cleanup-result.json") if (task / "state" / "risk-cleanup-result.json").exists() else {}
        if inv.get("blocking_risks", 0) and cleanup.get("total_remaining", 0):
            blocking.append("risk inventory has unresolved blocking risks")
    if (task / "state" / "full-order-audit.json").exists():
        audit = read_json(task / "state" / "full-order-audit.json")
        if audit.get("status") != "passed":
            blocking.append("full-order audit failed")
    if (task / "state" / "evidence-trace-ledger.json").exists():
        ledger = read_json(task / "state" / "evidence-trace-ledger.json")
        rewrite_pending = []
        for entry in ledger.get("entries", []):
            if entry.get("support_strength") == "analogy_only" and entry.get("final_decision") == "inserted":
                blocking.append(f"{entry.get('claim_id')} analogy_only inserted")
            if "ownership_unverified" in entry.get("risk_flags", []) and entry.get("final_decision") == "inserted":
                blocking.append(f"{entry.get('claim_id')} ownership_unverified inserted")
            if entry.get("final_decision") == "blocked_rewrite_required":
                rewrite_pending.append(entry.get("claim_id"))
        if rewrite_pending:
            blocking.append(f"writing-pool paragraph rewrites pending: {', '.join(str(x) for x in rewrite_pending)}")
    cleaned_refs_path = task / "state" / "cleaned-reference-list.json"
    cleaned_plan_path = task / "state" / "cleaned-insertion-plan.json"
    if cleaned_refs_path.exists() and cleaned_plan_path.exists():
        refs = {r.get("ref_id") for r in read_json(cleaned_refs_path).get("references", []) if r.get("ref_id")}
        consumed = {
            i.get("evidence_basis", {}).get("source_ref_id")
            for i in read_json(cleaned_plan_path).get("insertions", [])
            if i.get("evidence_basis", {}).get("source_ref_id")
        }
        unconsumed = sorted(refs - consumed)
        if unconsumed:
            blocking.append(f"cleaned references are unconsumed: {', '.join(unconsumed)}")
    delivery_path = task / "delivery"
    if delivery_path.exists():
        top_files = [p.name for p in delivery_path.iterdir() if p.is_file()]
        if len(top_files) > 10:
            blocking.append(f"delivery top-level has too many files: {len(top_files)}")
    status = "failed" if blocking else "passed"
    report = {"status": status, "blocking_issues": blocking, "warnings": warnings}
    out = task / "state" / "final-gate-result.json"
    write_json(out, report)
    update_flow_status(task, "S110", blocked=bool(blocking), note="; ".join(blocking[:3]) if blocking else "final gate passed")
    print_json(result(status if status == "passed" or not args.allow_fail else "passed", output=str(out), report=report))
    return 0 if status == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
