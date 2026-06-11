#!/usr/bin/env python3
"""Run or import the footnote thinking-pool result."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def infer_mock_decision(item: dict) -> dict:
    text = item.get("body_context", {}).get("target_sentence", "") or ""
    risks = item.get("known_risks", []) or []
    evidence = item.get("rag_evidence", {}) or {}
    claim_id = item.get("claim_id")
    if len(text) < 12 or "关键词" in text or text.endswith("示意图"):
        return {
            "order": item.get("order"),
            "claim_id": claim_id,
            "decision": "no_note",
            "confidence": 0.85,
            "no_note_reason": "该处不是需要脚注解释的正文论证点。",
        }
    if evidence.get("support_strength") == "partial_support":
        decision = "reference_only"
        return {
            "order": item.get("order"),
            "claim_id": claim_id,
            "decision": decision,
            "evidence_used": evidence_used(evidence),
            "confidence": min(float(evidence.get("confidence") or 0.7), 0.82),
            "reference_only_reason": "该处主要需要文献支撑，不需要另行解释正文概念。",
            "risk_flags": risks,
        }
    if evidence.get("support_strength") == "strong_support" and float(evidence.get("confidence") or 0) >= 0.85:
        proposed = make_mock_note(text, "concept")
        return {
            "order": item.get("order"),
            "claim_id": claim_id,
            "decision": "footnote_needed",
            "footnote_intent": "补足正文中概念或机制的必要解释，使读者理解该处论证前提。",
            "footnote_type": "concept",
            "proposed_note_text": proposed,
            "evidence_used": evidence_used(evidence),
            "why_not_reference_only": "该处不仅需要来源支撑，还需要把正文中的机制关系解释为读者可理解的补充说明。",
            "why_not_body_rewrite": "补充内容属于旁注式解释，放入脚注可避免打断正文主线。",
            "risk_flags": risks,
            "confidence": min(float(evidence.get("confidence") or 0.86), 0.9),
        }
    if any(key in text for key in ["又名", "是指", "所谓", "概念", "智能", "评价系统", "脱格", "中宫", "黄金分割", "方中有圆"]):
        note_type = "terminology" if "又名" in text else "concept"
        if "智能" in text or "评价系统" in text:
            note_type = "technical_premise"
        if "中宫" in text or "黄金分割" in text or "方中有圆" in text:
            note_type = "mechanism"
        proposed = make_mock_note(text, note_type)
        return {
            "order": item.get("order"),
            "claim_id": claim_id,
            "decision": "footnote_needed",
            "footnote_intent": "补足正文中术语或机制的必要解释，使读者在不跳转文献的情况下理解该处论证前提。",
            "footnote_type": note_type,
            "proposed_note_text": proposed,
            "evidence_used": evidence_used(evidence),
            "why_not_reference_only": "该处需要补充概念或机制含义，单列参考文献不能解决读者理解问题。",
            "why_not_body_rewrite": "补充内容属于前提性说明，放入脚注可保持正文论证节奏。",
            "risk_flags": risks,
            "confidence": min(max(float(evidence.get("confidence") or 0.75), 0.65), 0.9),
        }
    return {
        "order": item.get("order"),
        "claim_id": claim_id,
        "decision": "reference_only",
        "evidence_used": evidence_used(evidence),
        "confidence": min(float(evidence.get("confidence") or 0.72), 0.85),
        "reference_only_reason": "该处需要保留证据来源，但正文不存在必须由脚注补足的解释缺口。",
        "risk_flags": risks,
    }


def make_mock_note(text: str, note_type: str) -> str:
    if note_type == "terminology":
        return "此处术语用于统一指称同一习字格对象，避免因不同场景下的名称差异造成理解偏差；正文后续均按同一教学工具展开讨论。"
    if note_type == "technical_premise":
        return "智能评价通常需要先将习字纸中的字形区域转化为可分析图像，再提取结构、重心和笔画位置等特征，因此格线设计会影响后续识别与评价的稳定性。"
    if note_type == "mechanism":
        return "这里强调的是书写空间的结构参照作用：格线、中心点和圆形边界共同帮助学习者判断部件比例、重心位置和笔画伸展范围。"
    return "该概念在本文中主要作为教学支架使用，作用是把抽象的结构规律转化为学生能够观察、比较和迁移的书写参照。"


def evidence_used(evidence: dict) -> dict:
    return {
        "chunk_id": evidence.get("chunk_id"),
        "source_claim": (evidence.get("chunk_text") or "")[:120],
        "grounding_trace": evidence.get("grounding_summary") or evidence.get("grounding_status"),
        "source_ref_id": evidence.get("source_ref_id"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--result", type=Path, help="Import an externally produced thinking result JSON.")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    request_path = task / "state" / "footnote-thinking-request.json"
    if not request_path.exists():
        print_json(result("failed", blocker="missing_footnote_thinking_request", errors=["footnote-thinking-request.json missing"]))
        update_flow_status(task, "S67", status="failed", blocked=True, note="missing_footnote_thinking_request")
        return 1
    request = read_json(request_path)
    if args.result:
        data = read_json(args.result)
        data.setdefault("request_id", request.get("request_id"))
        data.setdefault("status", "completed")
    elif args.mock:
        data = {
            "result_id": f"{request.get('request_id')}-mock-result",
            "request_id": request.get("request_id"),
            "status": "completed",
            "mode": "mock",
            "results": [infer_mock_decision(item) for item in request.get("items", [])],
        }
    else:
        print_json(result("failed", blocker="thinking_pool_not_configured", errors=["provide --mock for fixtures or --result for external thinking-pool output"]))
        update_flow_status(task, "S67", status="failed", blocked=True, note="thinking_pool_not_configured")
        return 1
    out = task / "state" / "footnote-thinking-result.json"
    write_json(out, data)
    update_flow_status(task, "S67", note=f"footnote thinking results={len(data.get('results', []))}")
    print_json(result("passed", output=str(out), results=len(data.get("results", []))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
