#!/usr/bin/env python3
"""Build the offline delivery package."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import VERSION, copy_if_exists, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    final_gate_path = task / "state" / "final-gate-result.json"
    quality_path = task / "state" / "quality-report.json"
    if final_gate_path.exists():
        final_gate = read_json(final_gate_path)
        quality = {"status": final_gate.get("status", "unknown"), "source": "final-gate-result.json"}
    elif quality_path.exists():
        quality = read_json(quality_path)
        final_gate = {}
    else:
        print_json(result("failed", errors=["final-gate-result.json or quality-report.json missing"]))
        return 1
    delivery = task / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    process = delivery / "process"
    process.mkdir(parents=True, exist_ok=True)
    top_level = [
        "full-text-with-notes.md",
        "full-order-audit.md",
        "full-order-audit.json",
        "risk-inventory.json",
        "risk-cleanup-result.json",
        "evidence-trace-ledger.json",
        "final-gate-result.json",
    ]
    for name in top_level:
        copy_if_exists(task / "state" / name, delivery / name)
    for name in [
        "evidence-map.json", "insertion-plan.json", "cleaned-insertion-plan.json",
        "cleaned-citation-needs.json", "cleaned-reference-list.json",
        "quality-report.json", "intake-status.json",
        "search-blueprint.json", "intake-quality-gate.json",
        "footnote-candidate-pool.json", "footnote-pruning-result.json", "reference-pruning-plan.json",
        "authenticity-verification-request.json", "authenticity-verification-result.json",
        "authenticity-issues.json", "consistency-gate-result.json",
        "grounding-resolution.json", "markdown-verification.json", "pdf-fallback-verification.json",
        "writing-pool-review-request.json", "writing-pool-review-result.json", "writing-pool-gate-result.json",
        "risk-cleanup-plan.json", "still-needs-human-review.json", "cleaned-补库-needs.json",
    ]:
        copy_if_exists(task / "state" / name, process / name)
    evidence = read_json(task / "state" / "evidence-map.json")
    plan = read_json(task / "state" / "insertion-plan.json")
    intake_gate_path = task / "state" / "intake-quality-gate.json"
    intake_gate = read_json(intake_gate_path) if intake_gate_path.exists() else {}
    human_review = {
        "page_numbers_to_verify": [i for i in plan["insertions"] if "page_missing" in i["evidence_basis"].get("risks", [])],
        "rewrite_suggestions": [i for i in plan["insertions"] if i.get("requires_rewrite")],
        "risk_citations": [i for i in plan["insertions"] if i["evidence_basis"].get("risks")],
        "authenticity_issues": read_json(task / "state" / "authenticity-issues.json").get("issues", []) if (task / "state" / "authenticity-issues.json").exists() else [],
        "no_support_critical": evidence.get("critical_gaps", []),
        "high_risk_unsupported": evidence.get("high_risk_unsupported", []),
        "library_gap_directions": intake_gate.get("suggested_补充_directions", []),
        "grounding_unresolved": [i for i in plan["insertions"] if i.get("grounding_status") in {"unresolved_grounding", "chunk_only_grounding"}],
        "pdf_fallback_pending": [i for i in plan["insertions"] if i.get("grounding_status") == "pdf_fallback_required"],
    }
    unresolved = [gap for gap in evidence.get("critical_gaps", []) if gap.get("need_level") == "critical"]
    handoff = {
        "target_skill": "正文写作",
        "protocol_version": "1.0",
        "quality_status": quality["status"],
        "insertions": plan["insertions"],
        "no_insert_zones": plan["no_insert_zones"],
        "high_risk_unsupported": evidence.get("high_risk_unsupported", []),
        "unresolved_critical_claims": unresolved,
        "existing_references_merge_status": {
            "status": f"not_implemented_in_{VERSION}",
            "existing_references_verified": plan.get("reference_list", {}).get("existing_references_verified", []),
            "zotero_reference_master_merge": "pending_manual_or_writer_side_merge",
        },
        "library_status": "built" if (task / "state" / "intake-status.json").exists() else "not_built",
        "library_gap_directions": intake_gate.get("suggested_补充_directions", []),
        "grounding_summary": evidence.get("grounding_summary", {}),
        "manual_citation_tasks": human_review["page_numbers_to_verify"] + human_review["risk_citations"],
        "writer_consumption_notes": {
            "r2_a1_gap_routing": "unsupported critical/important claims may become gap-routing-table entries",
            "r2_a2_search_plan": "search-intake requests can be transformed into round2-search-plan rows",
            "citation_hygiene": "gbt7714_footnote and risks are provided for writer-side citation checks",
            "footnote_boundary": "footnote/endnote text is only for necessary content supplements; reference_only entries must not become footnote prose",
        },
    }
    write_json(process / "human_review_needed.json", human_review)
    write_json(process / "handoff_to_writing.json", handoff)
    write_json(process / "statistics.json", {
        "insertions": len(plan["insertions"]),
        "no_insert_zones": len(plan["no_insert_zones"]),
        "references": len(plan.get("reference_list", {}).get("new_references", [])),
        "footnote_pruning_applied": plan.get("footnote_pruning_applied", False),
        "process_files_are_under": "process/",
    })
    (delivery / "summary.md").write_text(
        f"# ReferenceFootnote Delivery\n\nQuality status: {quality['status']}\n\n"
        "Top-level files are the main entry points. Process files are under `process/`.\n",
        encoding="utf-8",
    )
    (process / "changelog.md").write_text(f"# Citation Change Log\n\nGenerated offline by ReferenceFootnote {VERSION}.\n", encoding="utf-8")
    print_json(result("passed", output=str(delivery)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
