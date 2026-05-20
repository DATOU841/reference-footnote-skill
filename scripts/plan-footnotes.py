#!/usr/bin/env python3
"""Plan footnote and reference insertions from the evidence map."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    PROTECTED_TYPES,
    annotation_purpose_for,
    consumption_depth_for_strength,
    ensure_task,
    infer_evidence_type,
    infer_source_role,
    material_flag,
    necessity_score,
    print_json,
    read_json,
    result,
    write_json,
)


def footnote_text(ref: dict, style: str = "chinese_legal_journal") -> str:
    authors = "、".join(ref.get("authors", ["佚名"]))
    title = ref.get("title", "未题名文献")
    source = ref.get("source", "")
    year = ref.get("year", "")
    pages = ref.get("pages", "")
    if style in {"gb_t_7714", "gbt7714"}:
        return f"{authors}. {title}[J]. {source}, {year}: {pages}."
    return f"参见{authors}：《{title}》，载《{source}》{year}年，第{pages}页。"


def build_from_pruning(task: Path, style: str) -> dict | None:
    pruning_path = task / "state" / "footnote-pruning-result.json"
    reference_path = task / "state" / "reference-pruning-plan.json"
    evidence_path = task / "state" / "evidence-map.json"
    if not pruning_path.exists():
        return None
    pruning = read_json(pruning_path)
    evidence = read_json(evidence_path)
    references = read_json(reference_path).get("kept_references", []) if reference_path.exists() else []
    refs = {}
    insertions = []
    for item in pruning.get("kept", []):
        ref = item.get("reference", {})
        ref_id = ref.get("ref_id", item.get("candidate_id"))
        refs[ref_id] = ref
        gbt = footnote_text(ref, "gb_t_7714")
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
            "annotation_purpose": item.get("annotation_purpose", "evidence"),
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
                "text": item.get("candidate_note_text") if item.get("note_type") != "reference_only" else None,
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
        "pruning_audit": {"removed": pruning.get("removed", []), "warnings": pruning.get("warnings", [])},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--style", default="chinese_legal_journal")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    pruned_plan = build_from_pruning(task, args.style)
    if pruned_plan:
        out = task / "state" / "insertion-plan.json"
        write_json(out, pruned_plan)
        print_json(result("passed", output=str(out), insertions=len(pruned_plan["insertions"]), no_insert_zones=len(pruned_plan["no_insert_zones"])))
        return 0
    evidence_path = task / "state" / "evidence-map.json"
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    evidence = read_json(evidence_path)
    insertions = []
    no_insert = []
    refs = {}
    for entry in evidence["claim_evidence"]:
        if entry["claim_type"] in PROTECTED_TYPES or entry["evidence_status"] in {"no_support", "conflict", "not_needed"}:
            if entry["claim_type"] in PROTECTED_TYPES or entry["evidence_status"] in {"no_support", "conflict"}:
                no_insert.append({
                    "claim_id": entry["claim_id"],
                    "text": entry["text"],
                    "reason": f"{entry['claim_type']} / {entry['evidence_status']}",
                    "no_insert_reason": f"{entry['claim_type']} / {entry['evidence_status']}",
                    "writer_action": "标注为作者观点或人工复核，不得自动补注",
                    "rewrite_suggestion": None if entry["claim_type"] in PROTECTED_TYPES else "建议降低论断强度或补充来源后再处理。",
                })
            continue
        if entry["evidence_status"] in {"strong_support", "partial_support"} and entry.get("candidates"):
            cand = entry["candidates"][0]
            ref = cand.get("reference", {})
            ref_id = ref.get("ref_id", cand.get("candidate_id"))
            refs[ref_id] = ref
            grounding_status = cand.get("grounding_status", entry.get("grounding_status", "not_resolved"))
            risks = list(dict.fromkeys(cand.get("risks", [])))
            if grounding_status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
                risks.append("chunk_only_grounding")
            gbt = footnote_text(ref, "gb_t_7714")
            material = {"material_flag": material_flag(0), "usable_text_chars": 0}
            requires_rewrite = entry["evidence_status"] == "partial_support" or bool(risks) or grounding_status in {"chunk_only_grounding", "pdf_fallback_required", "unresolved_grounding"}
            insertions.append({
                "insertion_id": f"ins-{len(insertions)+1:03d}",
                "claim_id": entry["claim_id"],
                "claim_type": entry["claim_type"],
                "need_level": entry["need_level"],
                "note_type": "footnote",
                "annotation_purpose": annotation_purpose_for(entry, cand),
                "necessity_score": necessity_score(entry, cand, material),
                "material_flag": material["material_flag"],
                "usable_text_chars": material["usable_text_chars"],
                "authenticity_status": "not_checked",
                "pruning_reason": "legacy_direct_plan",
                "evidence_type": infer_evidence_type(entry["claim_type"], ref),
                "source_role": infer_source_role(entry["claim_type"], entry.get("citation_type")),
                "consumption_depth_suggestion": consumption_depth_for_strength(entry["evidence_status"], risks),
                "grounding_status": grounding_status,
                "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
                "footnote_content": {"style": args.style, "text": footnote_text(ref, args.style), "gbt7714_footnote": gbt},
                "gbt7714_footnote": gbt,
                "evidence_basis": {
                    "support_strength": entry["evidence_status"],
                    "confidence": cand.get("support_assessment", {}).get("confidence", 0),
                    "risks": risks,
                    "source_ref_id": ref_id,
                    "grounding_status": grounding_status,
                    "resolved_source": cand.get("grounding", {}).get("resolved_source"),
                },
                "requires_rewrite": requires_rewrite,
                "rewrite_suggestion": "建议限定表述、补充 Markdown/page map 核查或人工确认。" if requires_rewrite else None,
            })
    plan = {
        "article_id": evidence["article_id"],
        "style": args.style,
        "insertions": insertions,
        "no_insert_zones": no_insert,
        "reference_list": {"new_references": list(refs.values()), "existing_references_verified": []},
    }
    out = task / "state" / "insertion-plan.json"
    write_json(out, plan)
    print_json(result("passed", output=str(out), insertions=len(insertions), no_insert_zones=len(no_insert)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
