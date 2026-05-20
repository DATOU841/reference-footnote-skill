#!/usr/bin/env python3
"""Build a deterministic risk cleanup plan."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


ACTION_BY_RISK = {
    "ownership_unverified": "delete_note",
    "direct_experiment_missing": "downgrade_note",
    "secondhand_citation": "delete_note",
    "unconsumed_reference": "delete_reference",
    "analogy_as_strong": "downgrade_to_analogy_only",
    "rag_claim_mismatch": "delete_note",
    "writing_pool_rewrite_pending": "block_until_full_paragraph",
    "writing_pool_drop_pending": "delete_note",
    "page_missing": "mark_page_pending",
    "ocr_uncertain": "mark_ocr_uncertain",
    "concept_approximate": "revise_note_with_boundary",
    "no_pdf_no_markdown": "remove_from_final_references",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    inv_path = task / "state" / "risk-inventory.json"
    if not inv_path.exists():
        print_json(result("failed", errors=["risk-inventory.json missing"]))
        return 1
    inv = read_json(inv_path)
    actions = []
    for risk in inv.get("risks", []):
        action = ACTION_BY_RISK.get(risk.get("risk_type"), "human_review")
        actions.append({
            "risk_id": risk.get("risk_id"),
            "risk_type": risk.get("risk_type"),
            "severity": risk.get("severity"),
            "action": action,
            "claim_id": risk.get("claim_id"),
            "note_id": risk.get("current_note_id"),
            "reference_id": None,
            "requires_human_confirmation": action in {"block_until_full_paragraph", "human_review"},
        })
    data = {"cleanup_id": "cleanup-001", "source_risk_inventory": "risk-inventory.json", "actions": actions}
    out = task / "state" / "risk-cleanup-plan.json"
    write_json(out, data)
    update_flow_status(task, "S90", status="prepared", note=f"cleanup actions={len(actions)}")
    print_json(result("passed", output=str(out), actions=len(actions)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
