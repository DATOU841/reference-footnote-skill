#!/usr/bin/env python3
"""Validate thinking-pool footnote decisions before candidate planning."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    FOOTNOTE_TYPES,
    THINKING_DECISIONS,
    ensure_task,
    is_ai_defensive_note,
    is_evidence_relation_text,
    is_reference_format_text,
    print_json,
    read_json,
    result,
    update_flow_status,
    write_json,
)


def request_items_by_claim(request: dict) -> dict[str, dict]:
    return {item.get("claim_id"): item for item in request.get("items", []) if item.get("claim_id")}


def evidence_chunks_by_claim(evidence: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for entry in evidence.get("claim_evidence", []):
        claim_id = entry.get("claim_id")
        if not claim_id:
            continue
        chunks: set[str] = set()
        for cand in entry.get("candidates", []) or []:
            match = cand.get("match_details", {}) or {}
            for value in [cand.get("chunk_id"), cand.get("retrieved_chunk_id"), match.get("chunk_id")]:
                if value:
                    chunks.add(value)
        out[claim_id] = chunks
    return out


def rejection_reason(item: dict, request_item: dict | None, allowed_chunks: set[str] | None = None) -> str | None:
    decision = item.get("decision")
    if decision not in THINKING_DECISIONS:
        return "invalid_decision"
    confidence = float(item.get("confidence") or 0)
    if confidence < 0.6:
        return "confidence_below_threshold"
    if decision != "footnote_needed":
        return None
    text = (item.get("proposed_note_text") or "").strip()
    if len(text) < 30:
        return "proposed_note_text_too_short"
    if len(text) > 220:
        return "proposed_note_text_too_long"
    if is_reference_format_text(text):
        return "reference_format_in_footnote_body"
    if is_ai_defensive_note(text):
        return "ai_defensive_expression"
    if is_evidence_relation_text(text):
        return "evidence_relation_expression"
    if item.get("footnote_type") not in FOOTNOTE_TYPES:
        return "invalid_footnote_type"
    evidence_used = item.get("evidence_used") or {}
    if not evidence_used or not (evidence_used.get("chunk_id") or evidence_used.get("grounding_trace")):
        return "missing_evidence_used_trace"
    if not item.get("why_not_reference_only"):
        return "missing_why_not_reference_only"
    if not item.get("why_not_body_rewrite"):
        return "missing_why_not_body_rewrite"
    if request_item and evidence_used.get("chunk_id") and request_item.get("rag_evidence", {}).get("chunk_id"):
        allowed = allowed_chunks or {request_item.get("rag_evidence", {}).get("chunk_id")}
        if evidence_used.get("chunk_id") not in allowed:
            return "evidence_used_chunk_mismatch"
    return None


def merge_request_context(item: dict, request_item: dict | None) -> dict:
    request_item = request_item or {}
    merged = {**item}
    for key in ["paragraph_id", "sentence_id", "body_context", "claim_metadata", "rag_evidence", "consumable_literature", "known_risks"]:
        if key not in merged and key in request_item:
            merged[key] = request_item[key]
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    request_path = task / "state" / "footnote-thinking-request.json"
    result_path = task / "state" / "footnote-thinking-result.json"
    missing = [p.name for p in [request_path, result_path] if not p.exists()]
    if missing:
        print_json(result("failed", blocker="missing_footnote_thinking_result", errors=missing))
        update_flow_status(task, "S68", status="failed", blocked=True, note="missing_footnote_thinking_result")
        return 1
    request = read_json(request_path)
    data = read_json(result_path)
    lookup = request_items_by_claim(request)
    evidence_path = task / "state" / "evidence-map.json"
    evidence_chunks = evidence_chunks_by_claim(read_json(evidence_path)) if evidence_path.exists() else {}
    validated_footnotes = []
    validated_references = []
    rejected = []
    rewrite_needed = []
    human_review = []
    no_note = []
    for raw in data.get("results", []):
        req_item = lookup.get(raw.get("claim_id"))
        item = merge_request_context(raw, req_item)
        reason = rejection_reason(item, req_item, evidence_chunks.get(raw.get("claim_id")))
        if reason:
            rejected.append({**item, "rejection_reason": reason})
            continue
        decision = item.get("decision")
        if decision == "footnote_needed":
            validated_footnotes.append(item)
        elif decision == "reference_only":
            validated_references.append(item)
        elif decision == "rewrite_needed":
            rewrite_needed.append(item)
        elif decision == "human_review":
            human_review.append(item)
        elif decision == "no_note":
            no_note.append(item)
    warnings = []
    if not validated_footnotes and request.get("items"):
        warnings.append("no_valid_footnotes_generated")
    if len(validated_footnotes) > max(1, len(request.get("items", [])) * 0.3):
        warnings.append("footnote_needed_ratio_high")
    out_data = {
        "status": "passed",
        "request_id": request.get("request_id"),
        "result_id": data.get("result_id"),
        "validated_footnotes": validated_footnotes,
        "validated_references": validated_references,
        "rewrite_needed": rewrite_needed,
        "human_review": human_review,
        "no_note": no_note,
        "rejected": rejected,
        "warnings": warnings,
        "summary": {
            "validated_footnotes": len(validated_footnotes),
            "validated_references": len(validated_references),
            "rewrite_needed": len(rewrite_needed),
            "human_review": len(human_review),
            "no_note": len(no_note),
            "rejected": len(rejected),
        },
    }
    out = task / "state" / "footnote-thinking-validated.json"
    write_json(out, out_data)
    update_flow_status(task, "S68", note=f"validated footnotes={len(validated_footnotes)} references={len(validated_references)}")
    print_json(result("passed", output=str(out), **out_data["summary"], warnings=warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
