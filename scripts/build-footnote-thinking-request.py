#!/usr/bin/env python3
"""Build a full-order footnote thinking request from RAG-grounded evidence traces."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import PROTECTED_TYPES, ensure_task, print_json, read_json, result, update_flow_status, write_json


def article_index(article: dict) -> tuple[dict[str, dict], dict[str, tuple[str | None, str | None]]]:
    paragraphs = {p.get("paragraph_id"): p for p in article.get("paragraphs", [])}
    sentences: dict[str, tuple[str | None, str | None]] = {}
    for para in article.get("paragraphs", []):
        pid = para.get("paragraph_id")
        for sent in para.get("sentences", []):
            sentences[sent.get("sentence_id")] = (pid, sent.get("text"))
    return paragraphs, sentences


def context_for(article: dict, paragraph_id: str | None, sentence_id: str | None, fallback: str | None) -> dict:
    paragraphs, _sentences = article_index(article)
    para = paragraphs.get(paragraph_id or "", {})
    sents = para.get("sentences", [])
    idx = next((i for i, s in enumerate(sents) if s.get("sentence_id") == sentence_id), None)
    return {
        "target_sentence": (sents[idx].get("text") if idx is not None else fallback) or "",
        "preceding_context": sents[idx - 1].get("text") if idx is not None and idx > 0 else "",
        "following_context": sents[idx + 1].get("text") if idx is not None and idx + 1 < len(sents) else "",
        "paragraph_text": para.get("text", ""),
        "chapter_title": para.get("section_title") or para.get("section_id") or "",
    }


def evidence_by_claim(evidence: dict) -> dict[str, dict]:
    return {item.get("claim_id"): item for item in evidence.get("claim_evidence", []) if item.get("claim_id")}


def best_candidate(entry: dict) -> dict:
    candidates = entry.get("candidates", []) or []
    return candidates[0] if candidates else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--request-id", default="ft-thinking-001")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    article_path = task / "state" / "article-structure.json"
    evidence_path = task / "state" / "evidence-map.json"
    missing = [str(p.name) for p in [ledger_path, article_path, evidence_path] if not p.exists()]
    if missing:
        print_json(result("failed", blocker="missing_evidence_trace_for_thinking", errors=missing))
        update_flow_status(task, "S66", status="failed", blocked=True, note="missing_evidence_trace_for_thinking")
        return 1
    ledger = read_json(ledger_path)
    article = read_json(article_path)
    evidence = read_json(evidence_path)
    if not ledger.get("entries"):
        print_json(result("failed", blocker="missing_evidence_trace_for_thinking", errors=["evidence-trace-ledger entries empty"]))
        update_flow_status(task, "S66", status="failed", blocked=True, note="empty evidence trace")
        return 1
    evidence_lookup = evidence_by_claim(evidence)
    items = []
    skipped = []
    for entry in sorted(ledger.get("entries", []), key=lambda x: x.get("order", 0)):
        if entry.get("claim_type") in PROTECTED_TYPES:
            skipped.append({"claim_id": entry.get("claim_id"), "reason": "protected_claim_type"})
            continue
        if entry.get("support_strength") not in {"strong_support", "partial_support"}:
            skipped.append({"claim_id": entry.get("claim_id"), "reason": f"support_strength={entry.get('support_strength')}"})
            continue
        ev = evidence_lookup.get(entry.get("claim_id"), {})
        cand = best_candidate(ev)
        ref = cand.get("reference", {}) or {}
        support = cand.get("support_assessment", {}) or {}
        match = cand.get("match_details", {}) or {}
        chunk_text = cand.get("chunk_text") or match.get("snippet") or ""
        grounding = cand.get("grounding", {}) or {}
        grounding_status = cand.get("grounding_status") or ev.get("grounding_status") or entry.get("grounding_status")
        items.append({
            "order": entry.get("order"),
            "claim_id": entry.get("claim_id"),
            "paragraph_id": entry.get("paragraph_id"),
            "sentence_id": entry.get("sentence_id"),
            "body_context": context_for(article, entry.get("paragraph_id"), entry.get("sentence_id"), entry.get("original_text")),
            "claim_metadata": {
                "claim_type": entry.get("claim_type"),
                "need_level": entry.get("citation_need"),
                "citation_type": entry.get("citation_type"),
            },
            "rag_evidence": {
                "support_strength": entry.get("support_strength"),
                "confidence": support.get("confidence", 0),
                "chunk_id": cand.get("chunk_id") or match.get("chunk_id") or entry.get("retrieved_chunk_id"),
                "chunk_text": chunk_text,
                "source_ref_id": ref.get("ref_id") or entry.get("source_ref_id"),
                "grounding_status": grounding_status,
                "grounding_summary": grounding.get("grounding_status") or grounding_status,
                "resolved_source": grounding.get("resolved_source"),
            },
            "consumable_literature": {
                "topic": entry.get("original_text"),
                "source_ref_id": ref.get("ref_id"),
                "source_type": ref.get("source_type"),
                "key_concepts": [],
            },
            "known_risks": entry.get("risk_flags", []),
            "instruction": "判断此处正文是否有文中未尽而必要的解释需求；如有，基于 RAG 证据构思简洁、独立、非文献格式的脚注。",
        })
    out_data = {
        "request_id": args.request_id,
        "article_id": ledger.get("article_id"),
        "protocol_version": "1.0",
        "execution_status": "prepared_not_executed",
        "items": items,
        "skipped": skipped,
        "global_instruction": "大多数 claim 不需要脚注。只有正文确有未尽解释且读者必须知道时，才输出 footnote_needed。脚注不得列作者、文献题名、参考文献编号或 AI 防御式表述。",
    }
    out = task / "state" / "footnote-thinking-request.json"
    write_json(out, out_data)
    update_flow_status(task, "S66", note=f"footnote thinking request items={len(items)}")
    print_json(result("passed", output=str(out), items=len(items), skipped=len(skipped)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
