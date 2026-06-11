#!/usr/bin/env python3
"""Plan footnote and reference insertions from validated thinking candidates."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    FOOTNOTE_BARRED_PURPOSES,
    PROTECTED_TYPES,
    annotation_purpose_for,
    consumption_depth_for_strength,
    ensure_task,
    has_explanatory_content,
    infer_evidence_type,
    infer_source_role,
    is_ai_defensive_note,
    is_reference_format_text,
    material_flag,
    necessity_score,
    print_json,
    read_json,
    result,
    write_json,
)


def reference_citation_text(ref: dict, style: str = "chinese_legal_journal") -> str:
    authors = "、".join(ref.get("authors", ["佚名"]))
    title = ref.get("title", "未题名文献")
    source = ref.get("source", "")
    year = ref.get("year", "")
    pages = ref.get("pages", "")
    if style in {"gb_t_7714", "gbt7714"}:
        return f"{authors}. {title}[J]. {source}, {year}: {pages}."
    return f"参见{authors}：《{title}》，载《{source}》{year}年，第{pages}页。"


def valid_footnote_explanation(text: str | None) -> str | None:
    text = (text or "").strip()
    if not text:
        return None
    if is_ai_defensive_note(text) or is_reference_format_text(text):
        return None
    return text


def build_from_pruning(task: Path, style: str) -> dict | None:
    pruning_path = task / "state" / "footnote-pruning-result.json"
    reference_path = task / "state" / "reference-pruning-plan.json"
    evidence_path = task / "state" / "evidence-map.json"
    if not pruning_path.exists():
        return None
    pruning = read_json(pruning_path)
    if pruning.get("source_stage") != "S68_validated_thinking":
        return {
            "article_id": read_json(evidence_path).get("article_id") if evidence_path.exists() else None,
            "style": style,
            "insertions": [],
            "no_insert_zones": [],
            "reference_list": {"new_references": [], "existing_references_verified": []},
            "footnote_pruning_applied": True,
            "planning_blocker": "invalid_pruning_source_stage",
            "pruning_audit": {"removed": [], "warnings": [f"invalid source_stage: {pruning.get('source_stage')}"]},
        }
    evidence = read_json(evidence_path)
    references = read_json(reference_path).get("kept_references", []) if reference_path.exists() else []
    refs = {}
    insertions = []
    skipped = []
    for item in pruning.get("kept", []):
        purpose = item.get("annotation_purpose", "reference_only")
        note_text = valid_footnote_explanation(item.get("candidate_note_text"))
        if purpose in FOOTNOTE_BARRED_PURPOSES:
            skipped.append({"candidate_id": item.get("candidate_id"), "claim_id": item.get("claim_id"), "reason": f"annotation_purpose={purpose}_barred_from_insertion_plan"})
            continue
        if not note_text:
            skipped.append({"candidate_id": item.get("candidate_id"), "claim_id": item.get("claim_id"), "reason": "invalid_or_non_explanatory_footnote_text"})
            continue
        ref = item.get("reference", {})
        ref_id = ref.get("ref_id", item.get("candidate_id"))
        refs[ref_id] = ref
        gbt = reference_citation_text(ref, "gb_t_7714")
        grounding_status = item.get("grounding_status", "not_resolved")
        risks = list(dict.fromkeys(item.get("risks", [])))
        if grounding_status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
            risks.append("chunk_only_grounding")
        requires_rewrite = item.get("support_strength") == "partial_support" or bool(risks) or grounding_status in {"chunk_only_grounding", "pdf_fallback_required", "unresolved_grounding"}
        insertions.append({
            "insertion_id": f"ins-{len(insertions)+1:03d}",
            "candidate_id": item.get("candidate_id"),
            "claim_id": item["claim_id"],
            "claim_type": item["claim_type"],
            "need_level": item["need_level"],
            "note_type": item.get("note_type", "footnote"),
            "annotation_purpose": purpose,
            "necessity_score": item.get("necessity_score", 0),
            "material_flag": item.get("material_flag", "very_low"),
            "usable_text_chars": item.get("usable_text_chars", 0),
            "authenticity_status": item.get("authenticity_status", "not_checked"),
            "pruning_reason": item.get("pruning_reason", "kept"),
            "evidence_type": infer_evidence_type(item["claim_type"], ref),
            "source_role": infer_source_role(item["claim_type"]),
            "consumption_depth_suggestion": consumption_depth_for_strength(item.get("support_strength"), item.get("risks", [])),
            "grounding_status": grounding_status,
            "target_location": item["target_location"],
            "footnote_content": {
                "style": style,
                "text": note_text,
                "gbt7714_footnote": gbt,
            },
            "gbt7714_footnote": gbt,
            "evidence_basis": {
                "support_strength": item.get("support_strength"),
                "confidence": item.get("confidence", 0),
                "risks": risks,
                "source_ref_id": ref_id,
                "evidence_source": item.get("evidence_source", "rag_verified"),
                "grounding_status": grounding_status,
                "resolved_source": item.get("resolved_source") or item.get("grounding", {}).get("resolved_source"),
            },
            "requires_rewrite": requires_rewrite,
            "rewrite_suggestion": "建议限定表述、补充 Markdown/page map 核查或人工确认。" if requires_rewrite else None,
        })
    no_insert = [
        {
            "claim_id": entry["claim_id"],
            "text": entry["text"],
            "reason": f"{entry['claim_type']} / {entry['evidence_status']}",
            "no_insert_reason": f"{entry['claim_type']} / {entry['evidence_status']}",
            "writer_action": "不得自动补注；必要时交人工或检索入库补库。",
            "rewrite_suggestion": None if entry["claim_type"] in PROTECTED_TYPES else "建议降低论断强度或补充来源后再处理。",
        }
        for entry in evidence.get("claim_evidence", [])
        if entry["claim_type"] in PROTECTED_TYPES or entry["evidence_status"] in {"no_support", "conflict"}
    ]
    if references:
        refs = {item["reference"].get("ref_id", f"ref-{idx:03d}"): item["reference"] for idx, item in enumerate(references, start=1)}
    return {
        "article_id": evidence["article_id"],
        "style": style,
        "insertions": insertions,
        "no_insert_zones": no_insert,
        "reference_list": {
            "new_references": list(refs.values()),
            "existing_references_verified": [],
            "reference_pruning_applied": reference_path.exists(),
        },
        "footnote_pruning_applied": True,
        "pruning_audit": {"removed": pruning.get("removed", []), "warnings": pruning.get("warnings", []), "skipped_after_frontgate": skipped},
    }


def build_from_candidate_pool(task: Path, style: str) -> dict | None:
    pool_path = task / "state" / "footnote-candidate-pool.json"
    reference_path = task / "state" / "reference-pruning-plan.json"
    evidence_path = task / "state" / "evidence-map.json"
    if not pool_path.exists():
        return None
    pool = read_json(pool_path)
    if pool.get("source_stage") != "S68_validated_thinking":
        return {
            "article_id": pool.get("article_id"),
            "style": style,
            "insertions": [],
            "no_insert_zones": [],
            "reference_list": {"new_references": [], "existing_references_verified": []},
            "footnote_pruning_applied": False,
            "planning_blocker": "invalid_candidate_pool_source_stage",
            "planning_audit": {"skipped_after_frontgate": [], "warnings": [f"invalid source_stage: {pool.get('source_stage')}"]},
        }
    evidence = read_json(evidence_path) if evidence_path.exists() else {"article_id": pool.get("article_id"), "claim_evidence": []}
    references = read_json(reference_path).get("kept_references", []) if reference_path.exists() else []
    refs = {}
    insertions = []
    skipped = []
    for item in pool.get("candidates", []):
        purpose = item.get("annotation_purpose", "reference_only")
        note_text = valid_footnote_explanation(item.get("candidate_note_text"))
        if purpose in FOOTNOTE_BARRED_PURPOSES:
            skipped.append({"candidate_id": item.get("candidate_id"), "claim_id": item.get("claim_id"), "reason": f"annotation_purpose={purpose}_barred_from_insertion_plan"})
            continue
        if not note_text:
            skipped.append({"candidate_id": item.get("candidate_id"), "claim_id": item.get("claim_id"), "reason": "invalid_or_non_explanatory_footnote_text"})
            continue
        ref = item.get("reference", {})
        ref_id = ref.get("ref_id", item.get("candidate_id"))
        refs[ref_id] = ref
        gbt = reference_citation_text(ref, "gb_t_7714")
        grounding_status = item.get("grounding_status", "not_resolved")
        risks = list(dict.fromkeys(item.get("risks", [])))
        if grounding_status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
            risks.append("chunk_only_grounding")
        requires_rewrite = item.get("support_strength") == "partial_support" or bool(risks) or grounding_status in {"chunk_only_grounding", "pdf_fallback_required", "unresolved_grounding"}
        insertions.append({
            "insertion_id": f"ins-{len(insertions)+1:03d}",
            "candidate_id": item.get("candidate_id"),
            "claim_id": item["claim_id"],
            "claim_type": item["claim_type"],
            "need_level": item["need_level"],
            "note_type": item.get("note_type", "footnote"),
            "annotation_purpose": purpose,
            "footnote_type": item.get("footnote_type"),
            "necessity_score": item.get("necessity_score", 0),
            "material_flag": item.get("material_flag", "very_low"),
            "usable_text_chars": item.get("usable_text_chars", 0),
            "authenticity_status": item.get("authenticity_status", "not_checked"),
            "pruning_reason": "candidate_pool_direct_plan",
            "evidence_type": infer_evidence_type(item["claim_type"], ref),
            "source_role": infer_source_role(item["claim_type"]),
            "consumption_depth_suggestion": consumption_depth_for_strength(item.get("support_strength"), item.get("risks", [])),
            "grounding_status": grounding_status,
            "target_location": item["target_location"],
            "footnote_content": {"style": style, "text": note_text, "gbt7714_footnote": gbt},
            "gbt7714_footnote": gbt,
            "evidence_basis": {
                "support_strength": item.get("support_strength"),
                "confidence": item.get("confidence", 0),
                "risks": risks,
                "source_ref_id": ref_id,
                "evidence_source": item.get("evidence_source", "rag_verified"),
                "grounding_status": grounding_status,
                "resolved_source": item.get("resolved_source") or item.get("grounding", {}).get("resolved_source"),
                "thinking_evidence_used": item.get("thinking_evidence_used"),
            },
            "requires_rewrite": requires_rewrite,
            "rewrite_suggestion": "建议限定表述、补充 Markdown/page map 核查或人工确认。" if requires_rewrite else None,
        })
    if references:
        refs = {item["reference"].get("ref_id", f"ref-{idx:03d}"): item["reference"] for idx, item in enumerate(references, start=1)}
    return {
        "article_id": evidence.get("article_id"),
        "style": style,
        "insertions": insertions,
        "no_insert_zones": [],
        "reference_list": {
            "new_references": list(refs.values()),
            "existing_references_verified": [],
            "reference_pruning_applied": reference_path.exists(),
        },
        "footnote_pruning_applied": False,
        "planning_audit": {"skipped_after_frontgate": skipped},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--style", default="chinese_legal_journal")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    pruned_plan = build_from_pruning(task, args.style)
    if pruned_plan:
        if pruned_plan.get("planning_blocker"):
            print_json(result("failed", blocker=pruned_plan["planning_blocker"], errors=pruned_plan.get("pruning_audit", {}).get("warnings", [])))
            return 1
        out = task / "state" / "insertion-plan.json"
        write_json(out, pruned_plan)
        print_json(result("passed", output=str(out), insertions=len(pruned_plan["insertions"]), no_insert_zones=len(pruned_plan["no_insert_zones"])))
        return 0
    plan = build_from_candidate_pool(task, args.style)
    if plan is None:
        print_json(result("failed", blocker="missing_footnote_candidate_pool", errors=["footnote-candidate-pool.json missing; run S66-S70a first"]))
        return 1
    if plan.get("planning_blocker"):
        print_json(result("failed", blocker=plan["planning_blocker"], errors=plan.get("planning_audit", {}).get("warnings", [])))
        return 1
    out = task / "state" / "insertion-plan.json"
    write_json(out, plan)
    print_json(result("passed", output=str(out), insertions=len(plan["insertions"]), no_insert_zones=len(plan["no_insert_zones"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
