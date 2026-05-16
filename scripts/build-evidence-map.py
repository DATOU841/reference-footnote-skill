#!/usr/bin/env python3
"""Build the citation evidence map."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    needs_path = task / "state" / "citation-needs.json"
    if not needs_path.exists():
        print_json(result("failed", errors=["citation-needs.json missing"]))
        return 1
    needs = read_json(needs_path)
    interp_by_claim = {}
    for path in sorted((task / "state" / "evidence-interpretations").glob("*.json")):
        for item in read_json(path).get("interpretations", []):
            interp_by_claim[item["claim_id"]] = item
    summary = {k: 0 for k in ["strong_support", "partial_support", "background_only", "conflict", "no_support", "not_needed"]}
    entries = []
    critical_gaps = []
    high_risk = []
    for need in needs["needs"]:
        interp = interp_by_claim.get(need["claim_id"])
        if need["need_level"] == "not_needed":
            strength = "not_needed"
            risks = []
            candidates = []
        elif interp:
            strength = interp.get("best_strength", "no_support")
            risks = interp.get("risks", [])
            candidates = interp.get("candidates", [])
        else:
            strength = "no_support"
            risks = []
            candidates = []
        summary[strength] = summary.get(strength, 0) + 1
        entry = {**need, "evidence_status": strength, "risks": risks, "candidates": candidates}
        entries.append(entry)
        if strength == "no_support" and need["need_level"] in {"critical", "important"}:
            critical_gaps.append(entry)
        if risks or strength == "conflict":
            high_risk.append(entry)
    out_data = {
        "article_id": needs["article_id"],
        "total_claims": len(entries),
        "coverage_summary": summary,
        "claim_evidence": entries,
        "critical_gaps": critical_gaps,
        "high_risk_unsupported": high_risk,
    }
    out = task / "state" / "evidence-map.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), critical_gaps=len(critical_gaps)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
