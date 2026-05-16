#!/usr/bin/env python3
"""Build the offline delivery package."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import copy_if_exists, ensure_task, print_json, read_json, result, write_json


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
    for name in ["evidence-map.json", "insertion-plan.json", "quality-report.json", "intake-status.json"]:
        copy_if_exists(task / "state" / name, delivery / name)
    evidence = read_json(task / "state" / "evidence-map.json")
    plan = read_json(task / "state" / "insertion-plan.json")
    human_review = {
        "page_numbers_to_verify": [i for i in plan["insertions"] if "page_missing" in i["evidence_basis"].get("risks", [])],
        "rewrite_suggestions": [i for i in plan["insertions"] if i.get("requires_rewrite")],
        "risk_citations": [i for i in plan["insertions"] if i["evidence_basis"].get("risks")],
        "no_support_critical": evidence.get("critical_gaps", []),
    }
    handoff = {"target_skill": "正文写作", "insertions": plan["insertions"], "no_insert_zones": plan["no_insert_zones"], "quality_status": quality["status"]}
    write_json(delivery / "human_review_needed.json", human_review)
    write_json(delivery / "handoff_to_writing.json", handoff)
    write_json(delivery / "statistics.json", {"insertions": len(plan["insertions"]), "no_insert_zones": len(plan["no_insert_zones"])})
    (delivery / "summary.md").write_text(f"# ReferenceFootnote Delivery\n\nQuality status: {quality['status']}\n", encoding="utf-8")
    (delivery / "changelog.md").write_text("# Citation Change Log\n\nGenerated offline by ReferenceFootnote 0.1.0-dev.\n", encoding="utf-8")
    print_json(result("passed", output=str(delivery)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
