#!/usr/bin/env python3
"""Build a footnote candidate pool from the evidence map."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    PROTECTED_TYPES,
    annotation_purpose_for,
    ensure_task,
    material_flag,
    necessity_score,
    print_json,
    read_json,
    result,
    write_json,
)


def material_by_claim(task: Path) -> dict:
    path = task / "state" / "intake-status.json"
    if not path.exists():
        return {}
    data = read_json(path)
    return {
        item.get("claim_id"): {
            "usable_text_chars": int(item.get("usable_text_chars") or 0),
            "usable_text_source": item.get("usable_text_source", "not_reported"),
            "material_flag": item.get("material_flag") or material_flag(item.get("usable_text_chars")),
        }
        for item in data.get("results", [])
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    evidence_path = task / "state" / "evidence-map.json"
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    evidence = read_json(evidence_path)
    materials = material_by_claim(task)
    candidates = []
    rejected = []
    for entry in evidence.get("claim_evidence", []):
        if entry.get("claim_type") in PROTECTED_TYPES or entry.get("evidence_status") in {"no_support", "not_needed"}:
            rejected.append({"claim_id": entry.get("claim_id"), "reason": f"{entry.get('claim_type')} / {entry.get('evidence_status')}"})
            continue
        if entry.get("evidence_status") not in {"strong_support", "partial_support", "background_only", "conflict"}:
            continue
        for cand in entry.get("candidates", [])[:2]:
            ref = cand.get("reference", {})
            support = cand.get("support_assessment", {})
            risks = cand.get("risks", entry.get("risks", []))
            purpose = annotation_purpose_for(entry, cand)
            note_type = "footnote" if purpose != "reference_only" else "reference_only"
            mat = materials.get(entry.get("claim_id"), {"usable_text_chars": 0, "usable_text_source": "not_reported", "material_flag": "very_low"})
            candidates.append({
                "candidate_id": f"fnc-{len(candidates)+1:03d}",
                "claim_id": entry["claim_id"],
                "claim_type": entry["claim_type"],
                "need_level": entry["need_level"],
                "text": entry["text"],
                "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
                "reference": ref,
                "note_type": note_type,
                "annotation_purpose": purpose,
                "support_strength": support.get("strength", entry.get("evidence_status")),
                "confidence": support.get("confidence", 0),
                "risks": risks,
                "usable_text_chars": mat["usable_text_chars"],
                "usable_text_source": mat["usable_text_source"],
                "material_flag": mat["material_flag"],
                "necessity_score": necessity_score(entry, cand, mat),
                "candidate_note_text": support.get("reasoning") or "需结合原文片段撰写必要补充说明。",
                "authenticity_status": "not_checked",
            })
    candidates.sort(key=lambda item: item["necessity_score"], reverse=True)
    out_data = {
        "article_id": evidence.get("article_id"),
        "target_candidate_range": {"min": 15, "max": 25},
        "candidates": candidates[:25],
        "rejected_before_pool": rejected,
        "pool_notes": "候选脚注必须是正文必要补充；reference_only 不得进入脚注正文。",
    }
    out = task / "state" / "footnote-candidate-pool.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), candidates=len(out_data["candidates"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
