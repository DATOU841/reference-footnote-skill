#!/usr/bin/env python3
"""Prune footnote candidates by necessity and boundary rules."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ANNOTATION_PURPOSES, NOTE_TYPES, ensure_task, print_json, read_json, result, write_json


def prune_reason(item: dict, seen_claims: set[str]) -> str | None:
    if item.get("note_type") not in NOTE_TYPES:
        return "invalid_note_type"
    if item.get("annotation_purpose") not in ANNOTATION_PURPOSES:
        return "invalid_annotation_purpose"
    if item.get("annotation_purpose") == "reference_only" and item.get("note_type") in {"footnote", "endnote"}:
        return "reference_only_barred_from_footnote_body"
    if item.get("annotation_purpose") == "background" and item.get("necessity_score", 0) < 55:
        return "background_without_necessary_supplement"
    if item.get("claim_id") in seen_claims and item.get("need_level") != "critical":
        return "duplicate_claim_kept_stronger_candidate"
    if item.get("material_flag") == "very_low" and item.get("need_level") != "critical":
        return "very_low_material_noncritical"
    if item.get("necessity_score", 0) < 35:
        return "low_necessity_score"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--target", type=int, default=15)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    path = task / "state" / "footnote-candidate-pool.json"
    if not path.exists():
        print_json(result("failed", errors=["footnote-candidate-pool.json missing"]))
        return 1
    pool = read_json(path)
    kept = []
    removed = []
    seen_claims: set[str] = set()
    for item in sorted(pool.get("candidates", []), key=lambda x: x.get("necessity_score", 0), reverse=True):
        reason = prune_reason(item, seen_claims)
        if reason:
            removed.append({**item, "pruning_reason": reason})
            continue
        if len(kept) >= max(args.target, 1) and item.get("need_level") != "critical":
            removed.append({**item, "pruning_reason": "outside_target_count_after_priority_sort"})
            continue
        kept.append({**item, "pruning_reason": "kept"})
        seen_claims.add(item.get("claim_id"))
    status = "passed"
    warnings = []
    if len(kept) < 10:
        warnings.append("footnote_count_low")
    if len(kept) > 20:
        status = "failed"
        warnings.append("footnote_count_excessive")
    out_data = {
        "status": status,
        "target_final_count": args.target,
        "kept": kept,
        "removed": removed,
        "warnings": warnings,
    }
    out = task / "state" / "footnote-pruning-result.json"
    write_json(out, out_data)
    print_json(result("failed" if status == "failed" else "passed", output=str(out), kept=len(kept), removed=len(removed), warnings=warnings))
    return 1 if status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
