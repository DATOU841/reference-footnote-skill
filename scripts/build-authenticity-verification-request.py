#!/usr/bin/env python3
"""Build an offline request for Markdown-first citation authenticity verification."""

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
        grounding_status = ins.get("grounding_status") or ins.get("evidence_basis", {}).get("grounding_status") or "not_resolved"
        known_risks = ins.get("evidence_basis", {}).get("risks", [])
        checks_required = [
            "reference_exists",
            "bibliographic_metadata_matches_source_record",
            "markdown_or_parsed_text_contains_cited_content",
            "rag_chunk_matches_markdown_or_parsed_text",
            "claim_fit",
            "insertion_position_fit",
        ]
        if grounding_status == "page_mapped_grounding":
            checks_required.append("page_map_consistency")
        if grounding_status == "pdf_fallback_required" or any(r in known_risks for r in ["page_missing", "ocr_uncertain", "vertical_text", "table_complex", "figure_embedded", "formula_inline", "page_map_conflict"]):
            checks_required.extend([
                "pdf_fallback_reference_layout_check",
                "page_number_or_ocr_status",
            ])
        items.append({
            "insertion_id": ins["insertion_id"],
            "claim_id": ins["claim_id"],
            "target_location": ins["target_location"],
            "note_type": ins.get("note_type", "footnote"),
            "annotation_purpose": ins.get("annotation_purpose", "evidence"),
            "footnote_text": ins.get("footnote_content", {}).get("text"),
            "source_ref_id": ins.get("evidence_basis", {}).get("source_ref_id"),
            "support_strength": ins.get("evidence_basis", {}).get("support_strength"),
            "grounding_status": grounding_status,
            "resolved_source": ins.get("evidence_basis", {}).get("resolved_source"),
            "known_risks": known_risks,
            "checks_required": checks_required,
        })
    out_data = {
        "request_type": "footnote_authenticity_verification",
        "batch_id": args.batch_id,
        "execution_status": "prepared_not_executed",
        "target_executor": "检索入库/Markdown核验/RAG平台或人工",
        "items": items,
        "hard_boundary": "ReferenceFootnote 只生成复核请求，不直接获取 PDF 或运行 RAG。默认核查 MinerU/MU Markdown 或等价 parsed text；PDF 仅在版式、页码或 OCR 风险触发时作为 fallback。",
    }
    out = task / "state" / "authenticity-verification-request.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), items=len(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
