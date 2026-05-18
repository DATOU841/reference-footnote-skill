#!/usr/bin/env python3
"""Prune reference candidates to the most important consumed sources."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def ref_key(ref: dict) -> str:
    return ref.get("ref_id") or f"{ref.get('title')}::{ref.get('year')}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--target-max", type=int, default=30)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    pool_path = task / "state" / "footnote-candidate-pool.json"
    pruning_path = task / "state" / "footnote-pruning-result.json"
    if not pool_path.exists():
        print_json(result("failed", errors=["footnote-candidate-pool.json missing"]))
        return 1
    pool = read_json(pool_path)
    consumed = read_json(pruning_path).get("kept", []) if pruning_path.exists() else []
    consumed_ids = {ref_key(item.get("reference", {})) for item in consumed}
    scored = {}
    for item in pool.get("candidates", []):
        ref = item.get("reference", {})
        key = ref_key(ref)
        if not key or key == "None::None":
            continue
        base = item.get("necessity_score", 0)
        if key in consumed_ids:
            base += 25
        if item.get("need_level") == "critical":
            base += 15
        prev = scored.get(key, {})
        prev_score = prev.get("score", -1) if isinstance(prev, dict) else -1
        scored[key] = {"reference": ref, "score": max(prev_score, base), "consumed": key in consumed_ids}
    ranked = sorted(scored.values(), key=lambda x: x["score"], reverse=True)
    kept = ranked[:args.target_max]
    removed = [
        {**item, "pruning_reason": "unconsumed_or_lower_priority_reference"}
        for item in ranked[args.target_max:]
    ]
    warnings = []
    if len(kept) < 20:
        warnings.append("reference_count_low")
    if len(kept) > 35:
        warnings.append("reference_count_high")
    status = "failed" if len(kept) > 40 else "passed"
    out_data = {
        "status": status,
        "target_final_range": {"min": 25, "max": 30},
        "kept_references": kept,
        "removed_references": removed,
        "warnings": warnings,
    }
    out = task / "state" / "reference-pruning-plan.json"
    write_json(out, out_data)
    print_json(result(status, output=str(out), kept=len(kept), removed=len(removed), warnings=warnings))
    return 1 if status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
