#!/usr/bin/env python3
"""Build an offline request for PDF + RAG authenticity verification."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="authenticity-01")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    plan_path = task / "state" / "insertion-plan.json"
    if not plan_path.exists():
        print_json(result("failed", errors=["insertion-plan.json missing"]))
        return 1
    plan = read_json(plan_path)
    items = []
    for ins in plan.get("insertions", []):
        if ins.get("note_type") == "reference_only":
            continue
        items.append({
            "insertion_id": ins["insertion_id"],
            "claim_id": ins["claim_id"],
            "target_location": ins["target_location"],
            "note_type": ins.get("note_type", "footnote"),
            "annotation_purpose": ins.get("annotation_purpose", "evidence"),
            "footnote_text": ins.get("footnote_content", {}).get("text"),
            "source_ref_id": ins.get("evidence_basis", {}).get("source_ref_id"),
            "support_strength": ins.get("evidence_basis", {}).get("support_strength"),
            "known_risks": ins.get("evidence_basis", {}).get("risks", []),
            "checks_required": [
                "reference_exists",
                "bibliographic_metadata_matches_pdf",
                "pdf_contains_cited_content",
                "rag_snippet_matches_pdf",
                "page_number_or_ocr_status",
                "claim_fit",
                "insertion_position_fit",
            ],
        })
    out_data = {
        "request_type": "footnote_authenticity_verification",
        "batch_id": args.batch_id,
        "execution_status": "prepared_not_executed",
        "target_executor": "检索入库/PDF核验/RAG平台或人工",
        "items": items,
        "hard_boundary": "ReferenceFootnote 只生成复核请求，不直接获取 PDF 或运行 RAG。",
    }
    out = task / "state" / "authenticity-verification-request.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), items=len(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
