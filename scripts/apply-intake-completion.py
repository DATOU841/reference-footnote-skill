#!/usr/bin/env python3
"""Apply a synthetic search-intake completion payload."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, material_flag, pool_material_status, print_json, read_json, result, write_json


REQUIRED_RESULT_FIELDS = {"request_id", "claim_id", "status", "sources_found", "kb_routing", "pdf_status", "import_status"}
VALID_RESULT_STATUSES = {"completed", "partial", "failed", "ingested"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--completion", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    completion = read_json(args.completion)
    errors = []
    if completion.get("status") not in {"completed", "partial", "failed"}:
        errors.append("completion status must be completed, partial, or failed")
    if not completion.get("handoff_id"):
        errors.append("handoff_id missing")
    for idx, item in enumerate(completion.get("results", []), start=1):
        missing = sorted(REQUIRED_RESULT_FIELDS - set(item))
        if missing:
            errors.append(f"results[{idx}] missing fields: {', '.join(missing)}")
        if item.get("status") not in VALID_RESULT_STATUSES:
            errors.append(f"results[{idx}] invalid status: {item.get('status')}")
        if not isinstance(item.get("sources_found", []), list):
            errors.append(f"results[{idx}].sources_found must be a list")
    results = completion.get("results", [])
    total_chars = 0
    for item in results:
        chars = int(item.get("usable_text_chars") or 0)
        total_chars += chars
        item["usable_text_chars"] = chars
        item.setdefault("usable_text_source", "not_reported")
        item["material_flag"] = material_flag(chars)
    avg = total_chars / len(results) if results else 0
    completion["pool_avg_usable_text_chars"] = round(avg, 2)
    completion["pool_material_status"] = pool_material_status(avg)
    completion["material_warnings"] = [
        {
            "claim_id": item.get("claim_id"),
            "request_id": item.get("request_id"),
            "usable_text_chars": item.get("usable_text_chars", 0),
            "material_flag": item.get("material_flag"),
        }
        for item in results
        if item.get("material_flag") in {"very_low", "below_average"}
    ]
    out = task / "state" / "intake-status.json"
    write_json(out, completion)
    print_json(result("failed" if errors else "passed", output=str(out), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
