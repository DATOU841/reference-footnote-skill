#!/usr/bin/env python3
"""Validate footnote/endnote/reference boundaries and consistency."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ANNOTATION_PURPOSES, NOTE_TYPES, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    plan_path = task / "state" / "insertion-plan.json"
    if not plan_path.exists():
        print_json(result("failed", errors=["insertion-plan.json missing"]))
        return 1
    plan = read_json(plan_path)
    auth_path = task / "state" / "authenticity-verification-result.json"
    auth = read_json(auth_path) if auth_path.exists() else {"results": []}
    auth_by_id = {item.get("insertion_id"): item for item in auth.get("results", [])}
    blocking = []
    warnings = []
    refs = {ref.get("ref_id") for ref in plan.get("reference_list", {}).get("new_references", [])}
    consumed_refs = set()
    for ins in plan.get("insertions", []):
        note_type = ins.get("note_type")
        purpose = ins.get("annotation_purpose")
        ref_id = ins.get("evidence_basis", {}).get("source_ref_id")
        if note_type not in NOTE_TYPES:
            blocking.append(f"{ins.get('insertion_id')} invalid note_type")
        if purpose not in ANNOTATION_PURPOSES:
            blocking.append(f"{ins.get('insertion_id')} invalid annotation_purpose")
        if purpose == "reference_only" and note_type in {"footnote", "endnote"}:
            blocking.append(f"{ins.get('insertion_id')} reference_only cannot have footnote body")
        if note_type in {"footnote", "endnote"} and not ins.get("footnote_content", {}).get("text"):
            blocking.append(f"{ins.get('insertion_id')} missing supplement text")
        if ref_id:
            consumed_refs.add(ref_id)
            if refs and ref_id not in refs:
                warnings.append(f"{ins.get('insertion_id')} source not in reference list: {ref_id}")
        auth_item = auth_by_id.get(ins.get("insertion_id"))
        if auth_item and auth_item.get("authenticity_status") == "failed":
            blocking.append(f"{ins.get('insertion_id')} authenticity failed")
        elif auth_item and auth_item.get("authenticity_status") == "human_review":
            warnings.append(f"{ins.get('insertion_id')} authenticity needs human review")
    unconsumed = sorted(ref for ref in refs if ref and ref not in consumed_refs)
    if unconsumed:
        warnings.append(f"unconsumed references should be deleted or explained: {', '.join(unconsumed)}")
    status = "failed" if blocking else "passed"
    out_data = {
        "status": status,
        "blocking_issues": blocking,
        "warnings": warnings,
        "unconsumed_references": unconsumed,
    }
    out = task / "state" / "consistency-gate-result.json"
    write_json(out, out_data)
    print_json(result(status if status == "passed" or not args.allow_fail else "passed", output=str(out), report=out_data))
    return 0 if status == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
