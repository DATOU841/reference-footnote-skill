#!/usr/bin/env python3
"""Build an offline writing-pool-style review request for notes."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def paragraph_map(task: Path) -> dict[str, str]:
    path = task / "state" / "article-structure.json"
    if not path.exists():
        return {}
    article = read_json(path)
    return {p.get("paragraph_id"): p.get("text", "") for p in article.get("paragraphs", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--request-id", default="writing-pool-review-01")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    if not ledger_path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json missing"]))
        return 1
    ledger = read_json(ledger_path)
    paras = paragraph_map(task)
    items = []
    for entry in ledger.get("entries", []):
        if not entry.get("note_id"):
            continue
        risks = entry.get("risk_flags", [])
        questions = [
            "注释是否放在该正文位置最合适？",
            "注释是否是正文内容的必要补充，而不是参考文献堆砌？",
            "注释措辞是否与 RAG 支撑强度匹配？",
        ]
        if entry.get("support_strength") == "analogy_only":
            questions.append("该注释是否明确保持类比证据边界，避免写成直接实证？")
        if "ownership_unverified" in risks:
            questions.append("该注释是否避免把未核权属写成已核实事实？")
        items.append({
            "order": entry.get("order"),
            "insertion_id": entry.get("note_id"),
            "claim_id": entry.get("claim_id"),
            "paragraph_id": entry.get("paragraph_id"),
            "sentence_id": entry.get("sentence_id"),
            "body_context": paras.get(entry.get("paragraph_id"), entry.get("original_text")),
            "original_text": entry.get("original_text"),
            "current_note_text": entry.get("note_text"),
            "support_strength": entry.get("support_strength"),
            "grounding_status": entry.get("grounding_status"),
            "known_risks": risks,
            "references_consumed": [entry.get("reference_id")] if entry.get("reference_id") else [],
            "review_questions": questions,
        })
    data = {
        "request_type": "writing_pool_review",
        "request_id": args.request_id,
        "article_id": ledger.get("article_id"),
        "execution_status": "prepared_not_executed",
        "target_executor": "ReferenceFootnote 独立写作池能力",
        "review_scope": [
            "note_position_fit",
            "note_wording_fit",
            "body_claim_strength_fit",
            "rewrite_needed_as_full_paragraph_only",
        ],
        "items": items,
    }
    out = task / "state" / "writing-pool-review-request.json"
    write_json(out, data)
    update_flow_status(task, "S80", status="prepared", note=f"writing-pool review items={len(items)}")
    print_json(result("passed", output=str(out), items=len(items)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
