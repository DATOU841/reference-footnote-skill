#!/usr/bin/env python3
"""Build a footnote candidate pool from validated thinking-pool decisions."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    FOOTNOTE_BARRED_PURPOSES,
    ensure_task,
    material_flag,
    necessity_score,
    print_json,
    read_json,
    result,
    write_json,
)


PURPOSE_BY_FOOTNOTE_TYPE = {
    "concept": "clarification",
    "terminology": "clarification",
    "background": "background",
    "mechanism": "supplement",
    "technical_premise": "supplement",
    "boundary": "supplement",
}


def material_by_claim(task: Path) -> dict:
    path = task / "state" / "intake-status.json"
    if not path.exists():
        return {}
    data = read_json(path)
    materials = {}
    pool_avg = int(data.get("pool_avg_usable_text_chars") or data.get("library_build_summary", {}).get("pool_avg_usable_text_chars") or 0)
    pool_material = {
        "usable_text_chars": pool_avg,
        "usable_text_source": "pool_average_fallback",
        "material_flag": material_flag(pool_avg),
    }
    for item in data.get("results", []):
        material = {
            "usable_text_chars": int(item.get("usable_text_chars") or 0),
            "usable_text_source": item.get("usable_text_source", "not_reported"),
            "material_flag": item.get("material_flag") or material_flag(item.get("usable_text_chars")),
        }
        if item.get("claim_id"):
            materials[item.get("claim_id")] = material
        for claim_id in item.get("claim_ids", []) or []:
            materials[claim_id] = material
    if pool_avg:
        materials["__pool_average__"] = pool_material
    return materials


def default_evidence_source(task: Path) -> str:
    status_path = task / "state" / "status.json"
    if status_path.exists() and read_json(status_path).get("rag_library_status") == "user_declared_existing":
        return "user_declared_existing"
    return "rag_verified"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    thinking_path = task / "state" / "footnote-thinking-validated.json"
    evidence_path = task / "state" / "evidence-map.json"
    if not thinking_path.exists():
        print_json(result("failed", blocker="missing_thinking_validation", errors=["footnote-thinking-validated.json missing"]))
        return 1
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    thinking = read_json(thinking_path)
    evidence = read_json(evidence_path)
    materials = material_by_claim(task)
    evidence_source = default_evidence_source(task)
    candidates = []
    reference_candidates = []
    rejected = []
    evidence_by_claim = {entry.get("claim_id"): entry for entry in evidence.get("claim_evidence", []) if entry.get("claim_id")}
    for item in thinking.get("validated_footnotes", []):
        entry = evidence_by_claim.get(item.get("claim_id"), {})
        if not entry:
            rejected.append({"claim_id": item.get("claim_id"), "reason": "claim_not_found_in_evidence_map"})
            continue
        cand = (entry.get("candidates") or [{}])[0]
        ref = cand.get("reference", {})
        support = cand.get("support_assessment", {})
        grounding_status = item.get("rag_evidence", {}).get("grounding_status") or cand.get("grounding_status", entry.get("grounding_status", "not_resolved"))
        risks = list(dict.fromkeys((item.get("risk_flags") or []) + (item.get("known_risks") or []) + cand.get("risks", entry.get("risks", []))))
        if grounding_status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
            risks.append("chunk_only_grounding")
        purpose = PURPOSE_BY_FOOTNOTE_TYPE.get(item.get("footnote_type"), "supplement")
        if purpose in FOOTNOTE_BARRED_PURPOSES:
            rejected.append({"claim_id": item.get("claim_id"), "reason": f"annotation_purpose={purpose}_barred_from_footnote_pool"})
            continue
        mat = materials.get(item.get("claim_id")) or materials.get("__pool_average__") or {"usable_text_chars": 0, "usable_text_source": "not_reported", "material_flag": "very_low"}
        candidates.append({
            "candidate_id": f"fnc-{len(candidates)+1:03d}",
            "claim_id": entry["claim_id"],
            "claim_type": entry["claim_type"],
            "need_level": entry["need_level"],
            "text": entry["text"],
            "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
            "reference": ref,
            "note_type": "footnote",
            "annotation_purpose": purpose,
            "footnote_type": item.get("footnote_type"),
            "footnote_intent": item.get("footnote_intent"),
            "support_strength": support.get("strength", entry.get("evidence_status")),
            "grounding_status": grounding_status,
            "grounding": cand.get("grounding", {}),
            "resolved_source": cand.get("grounding", {}).get("resolved_source"),
            "evidence_source": evidence_source,
            "confidence": item.get("confidence", support.get("confidence", 0)),
            "risks": risks,
            "usable_text_chars": mat["usable_text_chars"],
            "usable_text_source": mat["usable_text_source"],
            "material_flag": mat["material_flag"],
            "necessity_score": necessity_score(entry, cand, mat) + 10,
            "candidate_note_text": item.get("proposed_note_text"),
            "thinking_evidence_used": item.get("evidence_used"),
            "why_not_reference_only": item.get("why_not_reference_only"),
            "why_not_body_rewrite": item.get("why_not_body_rewrite"),
            "authenticity_status": "not_checked",
        })
    for item in thinking.get("validated_references", []):
        entry = evidence_by_claim.get(item.get("claim_id"), {})
        if not entry:
            continue
        cand = (entry.get("candidates") or [{}])[0]
        ref = cand.get("reference", {})
        support = cand.get("support_assessment", {})
        mat = materials.get(item.get("claim_id")) or materials.get("__pool_average__") or {"usable_text_chars": 0, "usable_text_source": "not_reported", "material_flag": "very_low"}
        reference_candidates.append({
            "claim_id": entry["claim_id"],
            "claim_type": entry["claim_type"],
            "need_level": entry["need_level"],
            "text": entry["text"],
            "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
            "reference": ref,
            "annotation_purpose": "reference_only",
            "support_strength": support.get("strength", entry.get("evidence_status")),
            "grounding_status": item.get("rag_evidence", {}).get("grounding_status") or cand.get("grounding_status", entry.get("grounding_status", "not_resolved")),
            "grounding": cand.get("grounding", {}),
            "resolved_source": cand.get("grounding", {}).get("resolved_source"),
            "evidence_source": evidence_source,
            "confidence": item.get("confidence", support.get("confidence", 0)),
            "risks": list(dict.fromkeys((item.get("risk_flags") or []) + (item.get("known_risks") or []) + cand.get("risks", entry.get("risks", [])))),
            "usable_text_chars": mat["usable_text_chars"],
            "usable_text_source": mat["usable_text_source"],
            "material_flag": mat["material_flag"],
            "necessity_score": necessity_score(entry, cand, mat),
            "routing_reason": "thinking_decision_reference_only",
        })
    for entry in evidence.get("claim_evidence", []):
        if entry.get("evidence_status") not in {"strong_support", "partial_support"}:
            continue
        for cand in entry.get("candidates", [])[:2]:
            ref = cand.get("reference", {})
            support = cand.get("support_assessment", {})
            grounding_status = cand.get("grounding_status", entry.get("grounding_status", "not_resolved"))
            risks = list(dict.fromkeys(cand.get("risks", entry.get("risks", []))))
            if grounding_status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
                risks.append("chunk_only_grounding")
            mat = materials.get(entry.get("claim_id")) or materials.get("__pool_average__") or {"usable_text_chars": 0, "usable_text_source": "not_reported", "material_flag": "very_low"}
            reference_candidate = {
                "claim_id": entry["claim_id"],
                "claim_type": entry["claim_type"],
                "need_level": entry["need_level"],
                "text": entry["text"],
                "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
                "reference": ref,
                "annotation_purpose": "reference_only",
                "support_strength": support.get("strength", entry.get("evidence_status")),
                "grounding_status": grounding_status,
                "grounding": cand.get("grounding", {}),
                "resolved_source": cand.get("grounding", {}).get("resolved_source"),
                "evidence_source": evidence_source,
                "confidence": support.get("confidence", 0),
                "risks": risks,
                "usable_text_chars": mat["usable_text_chars"],
                "usable_text_source": mat["usable_text_source"],
                "material_flag": mat["material_flag"],
                "necessity_score": necessity_score(entry, cand, mat),
                "routing_reason": "evidence_map_reference_foundation",
            }
            reference_candidates.append(reference_candidate)
    candidates.sort(key=lambda item: item["necessity_score"], reverse=True)
    out_data = {
        "article_id": evidence.get("article_id"),
        "source_stage": "S68_validated_thinking",
        "target_candidate_range": {"min": 15, "max": 25},
        "candidates": candidates[:25],
        "rejected_before_pool": rejected,
        "pool_notes": "候选脚注必须是文中未尽而必要的补充说明；纯证据支撑、纯文献引用、AI自证表述不得进入此池。",
    }
    out = task / "state" / "footnote-candidate-pool.json"
    write_json(out, out_data)
    ref_out = task / "state" / "reference-candidate-pool.json"
    write_json(ref_out, {
        "article_id": evidence.get("article_id"),
        "source": "S68_validated_thinking_and_evidence_reference_foundation",
        "source_stage": "S68_validated_thinking",
        "candidates": reference_candidates,
        "pool_notes": "脚注前置门禁拦截的有效证据候选进入参考文献规划，不作为脚注正文。",
    })
    print_json(result("passed", output=str(out), reference_output=str(ref_out), candidates=len(out_data["candidates"]), reference_candidates=len(reference_candidates)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
