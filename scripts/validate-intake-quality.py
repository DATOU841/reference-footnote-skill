#!/usr/bin/env python3
"""Validate initial library intake quality before RAG reverse lookup."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def source_type_for(item: dict) -> str:
    meta = item.get("ref_metadata") or {}
    for key in ["source_type", "type"]:
        if item.get(key):
            return item[key]
        if meta.get(key):
            return meta[key]
    found = item.get("sources_found") or []
    if found and isinstance(found[0], dict):
        return found[0].get("source_type") or found[0].get("type") or "unknown"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    intake_path = task / "state" / "intake-status.json"
    blueprint_path = task / "state" / "search-blueprint.json"
    if not intake_path.exists() or not blueprint_path.exists():
        print_json(result("failed", errors=["intake-status.json or search-blueprint.json missing"]))
        return 1
    intake = read_json(intake_path)
    blueprint = read_json(blueprint_path)
    results = intake.get("results", [])
    summary = intake.get("library_build_summary", {})
    total = int(summary.get("total_sources_ingested") or len(results))
    rag_indexed = int(summary.get("rag_indexed_count") or sum(1 for item in results if item.get("import_status", {}).get("rag_indexed")))
    avg = float(summary.get("pool_avg_usable_text_chars") or intake.get("pool_avg_usable_text_chars") or 0)
    breakdown = summary.get("type_breakdown") or {}
    if not breakdown:
        for item in results:
            stype = source_type_for(item)
            breakdown[stype] = breakdown.get(stype, 0) + 1
    covered_types = [key for key, value in breakdown.items() if value]
    min_pool = int(blueprint.get("initial_pool_min_sources", 40) * 0.6)
    min_avg = int(blueprint.get("min_usable_text_avg_per_source", 200))
    min_types = int(blueprint.get("type_coverage_minimum", 3))
    blocking = []
    warnings = []
    if total < min_pool:
        blocking.append(f"initial library pool too small: {total} < {min_pool}")
    if avg < min_avg:
        blocking.append(f"pool average usable text below threshold: {avg} < {min_avg}")
    if len(covered_types) < min_types:
        blocking.append(f"source type coverage too narrow: {len(covered_types)} < {min_types}")
    if total and rag_indexed / total < 0.5:
        warnings.append("rag indexed ratio below 50%")
    suggested = []
    if blocking:
        for direction in blueprint.get("directions", []):
            suggested.append({
                "direction_id": direction.get("direction_id"),
                "name": direction.get("name"),
                "keywords_zh": direction.get("keywords_zh", []),
                "minimum_sources": direction.get("minimum_sources", 3),
            })
    status = "failed" if blocking else "passed"
    out_data = {
        "status": status,
        "metrics": {
            "total_sources_ingested": total,
            "minimum_pool_required": min_pool,
            "pool_avg_usable_text_chars": avg,
            "min_usable_text_avg_per_source": min_avg,
            "type_breakdown": breakdown,
            "type_coverage": len(covered_types),
            "type_coverage_minimum": min_types,
            "rag_indexed_count": rag_indexed,
            "rag_indexed_ratio": rag_indexed / total if total else 0,
        },
        "blocking": blocking,
        "warnings": warnings,
        "suggested_补充_directions": suggested,
    }
    out = task / "state" / "intake-quality-gate.json"
    write_json(out, out_data)
    print_json(result(status if status == "passed" or not args.allow_fail else "passed", output=str(out), report=out_data))
    return 0 if status == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
