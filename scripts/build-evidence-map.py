#!/usr/bin/env python3
"""Build the citation evidence map."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, normalize_support_strength, print_json, read_json, result, search_dimensions_for_text, write_json


def grounding_index(task: Path) -> tuple[dict[tuple[str, str], dict], dict[str, int]]:
    path = task / "state" / "grounding-resolution.json"
    summary = {k: 0 for k in [
        "full_markdown_grounding",
        "page_mapped_grounding",
        "chunk_only_grounding",
        "pdf_fallback_required",
        "unresolved_grounding",
        "not_resolved",
    ]}
    if not path.exists():
        return {}, summary
    data = read_json(path)
    by_key = {}
    for item in data.get("resolved_items", []):
        key = (item.get("claim_id"), item.get("candidate_id"))
        by_key[key] = item
    for key, value in (data.get("summary") or {}).items():
        summary[key] = value
    return by_key, summary


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
    library_status = "built" if (task / "state" / "intake-status.json").exists() else "not_built"
    interp_by_claim = {}
    for path in sorted((task / "state" / "evidence-interpretations").glob("*.json")):
        for item in read_json(path).get("interpretations", []):
            interp_by_claim[item["claim_id"]] = item
    grounding_by_key, grounding_summary = grounding_index(task)
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
            strength = normalize_support_strength(interp.get("best_strength", "no_support"))
            risks = interp.get("risks", [])
            candidates = []
            for idx, cand in enumerate(interp.get("candidates", []), start=1):
                candidate_id = cand.get("candidate_id") or f"{need['claim_id']}-cand-{idx:02d}"
                grounding = grounding_by_key.get((need["claim_id"], candidate_id), {})
                grounding_status = grounding.get("grounding_status", "not_resolved")
                merged_risks = list(dict.fromkeys([*(cand.get("risks", []) or []), *(grounding.get("risk_flags", []) or [])]))
                candidates.append({
                    **cand,
                    "candidate_id": candidate_id,
                    "risks": merged_risks,
                    "grounding_status": grounding_status,
                    "grounding": grounding or {"grounding_status": "not_resolved"},
                })
            if candidates:
                risks = candidates[0].get("risks", risks)
        else:
            strength = "no_support"
            risks = []
            candidates = []
        grounding_status = candidates[0].get("grounding_status", "not_resolved") if candidates else "not_resolved"
        summary[strength] = summary.get(strength, 0) + 1
        entry = {**need, "evidence_status": strength, "grounding_status": grounding_status, "risks": risks, "candidates": candidates, "search_dimensions": search_dimensions_for_text(need["text"])}
        entries.append(entry)
        if strength == "no_support" and need["need_level"] in {"critical", "important"}:
            critical_gaps.append(entry)
        if risks or strength == "conflict":
            high_risk.append(entry)
    out_data = {
        "article_id": needs["article_id"],
        "total_claims": len(entries),
        "coverage_summary": summary,
        "grounding_summary": grounding_summary,
        "claim_evidence": entries,
        "critical_gaps": critical_gaps,
        "high_risk_unsupported": high_risk,
        "library_status": library_status,
    }
    out = task / "state" / "evidence-map.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), critical_gaps=len(critical_gaps)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
