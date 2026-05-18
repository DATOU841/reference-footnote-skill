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
    quality_path = task / "state" / "quality-report.json"
    if not quality_path.exists():
        print_json(result("failed", errors=["quality-report.json missing"]))
        return 1
    quality = read_json(quality_path)
    delivery = task / "delivery"
    delivery.mkdir(parents=True, exist_ok=True)
    for name in [
        "evidence-map.json", "insertion-plan.json", "quality-report.json", "intake-status.json",
        "footnote-candidate-pool.json", "footnote-pruning-result.json", "reference-pruning-plan.json",
        "authenticity-verification-request.json", "authenticity-verification-result.json",
        "authenticity-issues.json", "consistency-gate-result.json",
    ]:
        copy_if_exists(task / "state" / name, delivery / name)
    evidence = read_json(task / "state" / "evidence-map.json")
    plan = read_json(task / "state" / "insertion-plan.json")
    human_review = {
        "page_numbers_to_verify": [i for i in plan["insertions"] if "page_missing" in i["evidence_basis"].get("risks", [])],
        "rewrite_suggestions": [i for i in plan["insertions"] if i.get("requires_rewrite")],
        "risk_citations": [i for i in plan["insertions"] if i["evidence_basis"].get("risks")],
        "authenticity_issues": read_json(task / "state" / "authenticity-issues.json").get("issues", []) if (task / "state" / "authenticity-issues.json").exists() else [],
        "no_support_critical": evidence.get("critical_gaps", []),
        "high_risk_unsupported": evidence.get("high_risk_unsupported", []),
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
        "writer_consumption_notes": {
            "r2_a1_gap_routing": "unsupported critical/important claims may become gap-routing-table entries",
            "r2_a2_search_plan": "search-intake requests can be transformed into round2-search-plan rows",
            "citation_hygiene": "gbt7714_footnote and risks are provided for writer-side citation checks",
            "footnote_boundary": "footnote/endnote text is only for necessary content supplements; reference_only entries must not become footnote prose",
        },
    }
    write_json(delivery / "human_review_needed.json", human_review)
    write_json(delivery / "handoff_to_writing.json", handoff)
    write_json(delivery / "statistics.json", {
        "insertions": len(plan["insertions"]),
        "no_insert_zones": len(plan["no_insert_zones"]),
        "references": len(plan.get("reference_list", {}).get("new_references", [])),
        "footnote_pruning_applied": plan.get("footnote_pruning_applied", False),
    })
    (delivery / "summary.md").write_text(f"# ReferenceFootnote Delivery\n\nQuality status: {quality['status']}\n", encoding="utf-8")
    (delivery / "changelog.md").write_text(f"# Citation Change Log\n\nGenerated offline by ReferenceFootnote {VERSION}.\n", encoding="utf-8")
    print_json(result("passed", output=str(delivery)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
