#!/usr/bin/env python3
"""Build a blocking/warning risk inventory from the evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json

BLOCKING_RISKS = {
    "ownership_unverified",
    "direct_experiment_missing",
    "secondhand_citation",
    "unconsumed_reference",
    "analogy_as_strong",
    "rag_claim_mismatch",
    "writing_pool_rewrite_pending",
    "writing_pool_drop_pending",
}


def add_risk(risks: list[dict], *, entry: dict, risk_type: str, severity: str, description: str, required_action: str) -> None:
    risks.append({
        "risk_id": f"risk-{len(risks)+1:03d}",
        "risk_type": risk_type,
        "severity": severity,
        "claim_id": entry.get("claim_id"),
        "paragraph_id": entry.get("paragraph_id"),
        "sentence_id": entry.get("sentence_id"),
        "original_text": entry.get("original_text"),
        "current_note_id": entry.get("note_id"),
        "current_note_text": entry.get("note_text"),
        "evidence_trace_order": entry.get("order"),
        "description": description,
        "required_action": required_action,
        "cleanup_options": cleanup_options(risk_type),
    })


def cleanup_options(risk_type: str) -> list[str]:
    return {
        "ownership_unverified": ["delete_note", "move_to_risk_appendix", "request_补库"],
        "direct_experiment_missing": ["downgrade_note", "request_补库"],
        "secondhand_citation": ["delete_note", "request_补库"],
        "unconsumed_reference": ["delete_reference"],
        "analogy_as_strong": ["downgrade_to_analogy_only", "delete_note"],
        "rag_claim_mismatch": ["delete_note", "revise_note", "request_补库"],
        "writing_pool_rewrite_pending": ["return_paragraph_to_writing_pool"],
        "writing_pool_drop_pending": ["delete_note"],
        "page_missing": ["mark_page_pending", "request_page_check"],
        "ocr_uncertain": ["mark_ocr_uncertain", "request_markdown_or_pdf_fallback"],
        "concept_approximate": ["revise_note_with_boundary", "downgrade_note"],
        "no_pdf_no_markdown": ["remove_from_final_references", "downgrade_to_background"],
    }.get(risk_type, ["human_review"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    if not ledger_path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json missing"]))
        return 1
    ledger = read_json(ledger_path)
    risks: list[dict] = []
    consumed = {e.get("reference_id") for e in ledger.get("entries", []) if e.get("reference_id") and e.get("final_decision") == "inserted"}
    plan_path = task / "state" / "insertion-plan.json"
    refs = []
    if plan_path.exists():
        refs = read_json(plan_path).get("reference_list", {}).get("new_references", [])
    for entry in ledger.get("entries", []):
        flags = set(entry.get("risk_flags", []))
        if "ownership_unverified" in flags:
            add_risk(risks, entry=entry, risk_type="ownership_unverified", severity="blocking", description="一手权属材料缺失。", required_action="delete_note_or_provide_primary_source")
        if "direct_experiment_missing" in flags:
            add_risk(risks, entry=entry, risk_type="direct_experiment_missing", severity="blocking", description="教学效果缺少直接实验支撑。", required_action="downgrade_to_analogy_or_request_gap_handoff")
        if "secondhand_citation" in flags:
            add_risk(risks, entry=entry, risk_type="secondhand_citation", severity="blocking", description="当前证据为二手转述。", required_action="verify_primary_or_delete_note")
        if "page_missing" in flags:
            add_risk(risks, entry=entry, risk_type="page_missing", severity="warning", description="页码缺失。", required_action="mark_page_pending_or_check")
        if "ocr_uncertain" in flags:
            add_risk(risks, entry=entry, risk_type="ocr_uncertain", severity="warning", description="OCR 或解析文本不确定。", required_action="request_markdown_or_pdf_fallback")
        if "concept_approximate" in flags:
            add_risk(risks, entry=entry, risk_type="concept_approximate", severity="warning", description="概念近似匹配。", required_action="revise_note_with_boundary")
        if entry.get("support_strength") == "analogy_only" and entry.get("final_decision") == "inserted":
            add_risk(risks, entry=entry, risk_type="analogy_as_strong", severity="blocking", description="类比证据被直接插入。", required_action="downgrade_or_delete_note")
        if entry.get("writing_pool_decision") == "return_paragraph_for_rewrite" and not entry.get("writing_pool_rewritten_paragraph"):
            add_risk(risks, entry=entry, risk_type="writing_pool_rewrite_pending", severity="blocking", description="写作池要求完整段落重写但未处理。", required_action="block_final_delivery")
        if entry.get("writing_pool_decision") == "drop_note":
            add_risk(risks, entry=entry, risk_type="writing_pool_drop_pending", severity="blocking", description="写作池要求删除注释。", required_action="delete_note")
    for ref in refs:
        ref_id = ref.get("ref_id")
        if ref_id and ref_id not in consumed:
            add_risk(risks, entry={"claim_id": None, "order": None, "original_text": ref.get("title")}, risk_type="unconsumed_reference", severity="blocking", description=f"参考文献未被正文或注释消费：{ref_id}", required_action="delete_reference")
    summary = {}
    for risk in risks:
        summary[risk["risk_type"]] = summary.get(risk["risk_type"], 0) + 1
    data = {
        "version": "0.5.2-dev",
        "total_risks": len(risks),
        "blocking_risks": sum(1 for r in risks if r["severity"] == "blocking"),
        "warning_risks": sum(1 for r in risks if r["severity"] != "blocking"),
        "risks": risks,
        "risk_type_summary": summary,
    }
    out = task / "state" / "risk-inventory.json"
    write_json(out, data)
    update_flow_status(task, "S85", blocked=data["blocking_risks"] > 0, note=f"blocking risks={data['blocking_risks']}")
    print_json(result("passed", output=str(out), blocking_risks=data["blocking_risks"], warning_risks=data["warning_risks"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
